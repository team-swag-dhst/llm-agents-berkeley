from anthropic import Anthropic
from anthropic.types import Message
import os
from dotenv import load_dotenv

load_dotenv()

def query_claude(messages: list, system: str, tools: list) -> Message:

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools
    )

    return response

def convert_pydantic_to_anthropic_schema(model):

    json_schema = model.model_json_schema()
    return {
            "name": json_schema["title"],
            "description": json_schema["description"],
            "input_schema": {
                "type": "object",
                "properties": json_schema["properties"],
            }
    }
