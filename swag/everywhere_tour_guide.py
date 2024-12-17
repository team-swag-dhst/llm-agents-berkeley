import anthropic
import os
import logging
from typing import  AsyncGenerator

from swag.assistant import Assistant 
from swag.tools import SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType
from swag.prompts import SamAssistantPrompt, SamAssistantPromptOneImage

logger = logging.getLogger(__name__)

async def run_everywhere_tour_guide(
        base_image: str,
        location: str,
        lat: float,
        lon: float,
        masked_image: str = "",
) -> AsyncGenerator[str, None]:
    # cache : dict[str, str] = {}

    if masked_image == "" or masked_image == base_image:
        logger.info("Running Everywhere Tour Guide with one image")
        masked_image = ""
        prompt = "Tell me about what I'm looking at."
        system = str(SamAssistantPromptOneImage(location=location, lat=lat, lon=lon))
    else:

        prompt = "Tell me about the object in the blue area surrounded by the white line."
        system = str(SamAssistantPrompt(location=location, lat=lat, lon=lon))

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tools = [SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType]
    logger.info(f"Running Everywhere Tour Guide with location: {location}, lat: {lat}, lon: {lon}")
    assistant = Assistant(
        client=client,
        model="claude-3-5-sonnet-latest",
        system=system,
        tools=tools
    )

    async for chunk in assistant(prompt=prompt, images=[base_image, masked_image]):
        yield chunk
