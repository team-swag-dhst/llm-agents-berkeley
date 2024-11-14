from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock, Message
from .tools import SearchInternet, search
import logging
import os
from dotenv import load_dotenv

load_dotenv()

def query_claude(messages: list, system: str, tools: list) -> Message:
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    logging.info("Querying making request to Claude")
    response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools
    )
    logging.info("Received response from Claude")

    return response

def claude_tool_use(
        system: str, 
        tools: list,
        messages: list,
) -> tuple[list[dict], bool, list]:

    response = query_claude(messages, system, tools)
    content = response.content
    messages.append({"role": "assistant", "content": content})
    tool_use = response.stop_reason == "tool_use"
    logging.info(f"Tool use: {tool_use}")
    for message in content:
        if type(message) is TextBlock:
            continue
        elif type(message) is ToolUseBlock:
            id = message.id
            logging.info(f"Making tool use request ({message.name})")
            search_result = search(SearchInternet(**message.input)) # type: ignore
            logging.info(f"Received tool use response ({message.name})")
            new_input = [{
                    "type": "tool_result",
                    "tool_use_id": id,
                    "content": search_result,
                    "is_error": False,
            }]
            messages.append({"role": "user", "content": new_input})

    return messages, tool_use, content


def convert_pydantic_to_anthropic_schema(model):

    json_schema = model.model_json_schema()

    anthropic_tool = {
            "name": json_schema["title"],
            "description": json_schema["description"],
            "input_schema": {
                "type": "object",
                "properties": json_schema["properties"],
            }
    }

    return anthropic_tool
