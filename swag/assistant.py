from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock
import base64
from swag.tools import ToolRegistry
import json
import logging

logger = logging.getLogger(__name__)


def convert_pydantic_to_anthropic_schema(model) -> Dict[str, Any]:
    json_schema = model.model_json_schema()
    return {
        "name": json_schema["title"],
        "description": json_schema["description"],
        "input_schema": {
            "type": "object",
            "properties": json_schema["properties"],
        },
    }


class Assistant:
    def __init__(
        self,
        client: AsyncAnthropic,
        model: str,
        system: Optional[str] = None,
        tools: List[Dict] = [],
        max_steps: int = 10,
    ):
        self.client = client
        self.model = model
        self.system = system
        self.max_steps = max_steps
        self.messages = []
        self.max_tokens = 1024
        self.define_tools(tools)

    def define_tools(self, tools: List[Any]):
        """Defines the tools available to the assistant."""
        if tools:
            self.tools = [convert_pydantic_to_anthropic_schema(tool) for tool in tools]
            self.tool_fns = {
                tool.__name__: ToolRegistry.get(tool.__name__)[0] for tool in tools
            }
        else:
            self.tools = []
            self.tool_fns = {}

    async def __call__(
        self,
        prompt: str | None = None,
        images: List[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        if len(self.messages) >= 2 * self.max_steps:
            yield f"\nMaximum number of steps {self.max_steps} reached. Please start a new conversation."
            return
        if prompt:
            message = {"role": "user", "content": [{"type": "text", "text": prompt}]}
            if images:
                for image in images:
                    message["content"].append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image,
                            },
                        }
                    )
            self.messages.append(message)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=self.tools or [],
                system=self.system or "",
                messages=self.messages,
            )
            
            self.messages.append({"role": "assistant", "content": response.content})

            for content in response.content:
                if isinstance(content, TextBlock):
                    logger.info(f"Assistant: {content.text}")
                    yield f"\n{content.text}"
                elif isinstance(content, ToolUseBlock):
                    yield f"\nMaking a call to tool function {content.name} with input {content.input}."
                    tool_function, tool_model = ToolRegistry.get(content.name)
                    is_error = False
                    try:
                        if tool_function:
                            if tool_model:
                                model_instance = tool_model(**content.input)
                                tool_result = tool_function(model_instance)
                            else:
                                tool_result = tool_function(**content.input)

                            yield "\nTool function executed successfully."
                        else:
                            raise ValueError(f"Tool function {content.name} not found")
                    except Exception as e:
                        is_error = True
                        tool_result = str(e)
                        yield "\nAn error occurred when trying to interact with the tool."
                    
                    logger.info("Tool result: %s", tool_result[:100])
                    new_input = [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": tool_result,
                        "is_error": is_error,
                    }]
                    self.messages.append({"role": "user", "content": new_input})


            if response.stop_reason == "tool_use":
                async for chunk in self():
                    yield chunk

        except Exception as e:
            yield json.dumps({"type": "error", "text": f"An error occurred: {str(e)}"})
            return

    @staticmethod
    def load_image_base64(file_path: Path) -> str:
        with open(file_path, "rb") as file:
            file_content = file.read()
        return base64.b64encode(file_content).decode("utf-8")
