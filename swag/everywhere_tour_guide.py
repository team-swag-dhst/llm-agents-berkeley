from pydantic import BaseModel, Field
import anthropic
import os
from typing import  AsyncGenerator

from swag.assistant import Assistant 
from swag.tools import SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType
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
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tools = [SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType]
    prompt = "Tell me about the object in the blue area surrounded by the white line."
    system = str(SamAssistantPrompt(location=location, lat=lat, lon=lon))


    assistant = Assistant(
        client=client,
        model="claude-3-5-sonnet-latest",
        system=system,
        tools=tools
    )

    async for chunk in assistant(prompt=prompt, images=[base_image, masked_image]):
        yield chunk
