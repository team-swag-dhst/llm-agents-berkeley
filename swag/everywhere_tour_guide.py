from pydantic import BaseModel, Field
import anthropic
import os
from typing import  AsyncGenerator, Any
import logging

from swag.assistant import convert_pydantic_to_anthropic_schema
from swag.tools import SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType, search_internet, read_website, search_for_nearby_places_of_type
from swag.prompts import SamAssistantPrompt

class EverywhereTourGuideRequest(BaseModel):
    base_image: str = Field( description="Base64 Encoded SS of the user's eyeballs")
    masked_image: str = Field(description="Base64 Encoded SS of the user's eyeballs with a blue area surrounded by a white line")
    location: str = Field(description="Location of the user")
    lat: float = Field(description="Latitude of the user")
    lon: float = Field(description="Longitude of the user")

async def run_everywhere_tour_guide(
        base_image: str,
        masked_image: str,
        location: str,
        lat: float,
        lon: float
) -> AsyncGenerator[str, None]:
    # cache : dict[str, str] = {}
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tools: list = [convert_pydantic_to_anthropic_schema(tool) for tool in [SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType]]
    messages: list = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "data": base_image,
                    "media_type": "image/jpeg"}
                },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "data": masked_image,
                    "media_type": "image/jpeg"
                    }
            },
            {
                "type": "text",
                "text": "Tell me about the object in the blue area surrounded by the white line."
            }
        ]
    }]
    system = str(SamAssistantPrompt(location=location, lat=lat, lon=lon))


    response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            system=system,
            max_tokens=1024,
            messages=messages,
            tools=tools
    )
    tool_use = response.stop_reason == "tool_use"
    messages.append({"role": "assistant", "content": response.content})

    while tool_use:
        tool_use = response.stop_reason == "tool_use"
        for c in response.content:
            if type(c) is anthropic.types.TextBlock:
                text = c.text
                logging.info(f"Assistant: {text}")
                yield text
            if type(c) is anthropic.types.ToolUseBlock:
                msg = f"\nMaking tool use request to {c.name} with input: {c.input}"
                logging.info(msg)
                yield msg
                try:
                    if c.name == "SearchInternet":
                        ipt = SearchInternet(**c.input) # type: ignore
                        tool_result = search_internet(ipt)
                    elif c.name == "ReadWebsite":
                        ipt = ReadWebsite(**c.input) # type: ignore
                        tool_result = read_website(ipt)
                    elif c.name == "SearchForNearbyPlacesOfType":
                        ipt = SearchForNearbyPlacesOfType(**c.input) # type: ignore
                        tool_result = search_for_nearby_places_of_type(ipt)
                    else:
                        raise ValueError(f"Unknown tool: {c.name}")

                    is_error = False
                except Exception as e:
                    tool_result = str(e)
                    is_error = True

                new_input = [{
                    "type": "tool_result",
                    "tool_use_id": c.id,
                    "content": tool_result,
                    "is_error": is_error,
                }]
                messages.append({"role": "user", "content": new_input})

        if tool_use:
            response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    system=system,
                    max_tokens=1024,
                    messages=messages,
                    tools=tools
            )
            messages.append({"role": "assistant", "content": response.content})

    yield "\nProcess complete."
