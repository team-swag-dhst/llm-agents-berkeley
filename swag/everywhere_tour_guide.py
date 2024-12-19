# everywhere_tour_guide.py
import anthropic
import logging
from typing import AsyncGenerator
import base64

from swags.assistant import Assistant
from swags.tools import SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType
from swag.prompts import SamAssistantPrompt, SamAssistantPromptOneImage

logger = logging.getLogger(__name__)

model_id = "claude-3-5-sonnet-latest"
client = anthropic.AsyncAnthropic()

def base64_encode_image(image_path=None, image_bytes=None):
    if image_path:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    elif image_bytes:
        return base64.b64encode(image_bytes).decode("utf-8")
    return None

async def run_everywhere_tour_guide(
    base_image: str,
    location: str,
    lat: float,
    lon: float,
    masked_image: str = "",
) -> AsyncGenerator[str, None]:
    # Decode the base64 images to bytes
    base_image_bytes = base64.b64decode(base_image)
    if masked_image:
        masked_image_bytes = base64.b64decode(masked_image)
    else:
        masked_image_bytes = None

    # Encode the image bytes to base64 for the API
    base_image_encoded = base64_encode_image(image_bytes=base_image_bytes)
    masked_image_encoded = (
        base64_encode_image(image_bytes=masked_image_bytes) if masked_image_bytes else ""
    )

    if not masked_image_encoded:
        logger.info("Running Everywhere Tour Guide with one image")
        prompt = "Tell me about what I'm looking at."
        system = str(SamAssistantPromptOneImage(location=location, lat=lat, lon=lon))
    else:
        prompt = (
            "Tell me about the object in the blue area surrounded by the white line."
        )
        system = str(SamAssistantPrompt(location=location, lat=lat, lon=lon))

    tools = [SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType]
    logger.info(
        f"Running Everywhere Tour Guide with location: {location}, lat: {lat}, lon: {lon}"
    )

    assistant = Assistant(
        client=client,
        model=model_id,
        system=system,
        tools=tools,
    )

    async for chunk in assistant(
        prompt=prompt, images=[base_image_encoded, masked_image_encoded] if masked_image_encoded else [base_image_encoded]
    ):
        if chunk["type"] == "message_delta" and chunk["delta"]["type"] == "text_delta":
            yield chunk["delta"]["text"]
