from typing import List, Dict, Any, Optional, AsyncGenerator
from pathlib import Path
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock
import base64
from swag.tools import ToolRegistry
import json
import logging


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
        prompt: str,
        images: list[str]|None = None,
        current_result: Any = None,
    ) -> AsyncGenerator[str, None]:
        logging.info(f"Prompt (Truncated): {prompt[:50]}")
        if len(self.messages) >= 2 * self.max_steps:
            yield f"Maximum number of steps {self.max_steps} reached. Please start a new conversation."
            return

        message = {"role": "user", "content": [{"type": "text", "text": prompt}]}
        self.messages.append(message)

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

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=self.tools or [],
                system=self.system or "",
                messages=self.messages,
            )

            assistant_message = {"role": "assistant", "content": []}

            for content in response.content:
                if isinstance(content, TextBlock):
                    assistant_message["content"].append(content.__dict__)
                    text = content.text
                    logging.info(f"Assistant: {text}")
                    yield text 

                elif isinstance(content, ToolUseBlock):
                    
                    tool_use = f"Making a call to tool function {content.name} with input {content.input}. "
                    logging.info(tool_use)
                    yield tool_use
                    tool_function, tool_model = ToolRegistry.get(content.name)
                    if tool_function:
                        if tool_model:
                            model_instance = tool_model(**content.input)
                            tool_result = tool_function(model_instance)
                        else:
                            tool_result = tool_function(**content.input)
                        result_content = {
                            "type": "text",
                            "text": f"Tool {content.name} result: {tool_result}",
                        }
                        assistant_message["content"].append(result_content)
                    else:
                        error_content = {
                            "type": "text",
                            "text": f"\nTool function {content.name} not found",
                        }
                        assistant_message["content"].append(error_content)
                        yield json.dumps(error_content)

            self.messages.append(assistant_message)

            if response.stop_reason == "tool_use":
                async for chunk in self(
                    prompt=f"Function {content.name} was called and returned a value of {tool_result}",
                    current_result=tool_result,
                ):
                    yield chunk

            else:
                final_response = "\n".join(
                    [
                        content["text"]
                        for content in assistant_message["content"]
                        if content["type"] == "text"
                    ]
                )
                # yield json.dumps({"type": "text", "text": final_response})

        except Exception as e:
            yield json.dumps({"type": "error", "text": f"An error occurred: {str(e)}"})

    @staticmethod
    def load_image_base64(file_path: Path) -> str:
        with open(file_path, "rb") as file:
            file_content = file.read()
        return base64.b64encode(file_content).decode("utf-8")
