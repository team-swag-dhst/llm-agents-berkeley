import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import base64
import anthropic
from swag.tools import SearchInternet, search, ReadWebsite, read, NearbyPlacesSearch, nearby_places_search
from swag.assistant import convert_pydantic_to_anthropic_schema
import os
from dotenv import load_dotenv

load_dotenv()

def run_sam_assistant(raw_img_path: str, masked_img_path: str, location: str|None, lat: float, lon: float):

    import os
    print(f"Raw image exists: {os.path.exists(raw_img_path)}")
    print(f"Masked image exists: {os.path.exists(masked_img_path)}")
    
    cache: dict[str, str] = {}

    with open(raw_img_path, "rb") as image_file:
        raw_image_data = base64.b64encode(image_file.read()).decode("utf-8")

    with open(masked_img_path, "rb") as image_file:
        masked_image_data = base64.b64encode(image_file.read()).decode("utf-8")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    tools: list = [convert_pydantic_to_anthropic_schema(tool) for tool in [SearchInternet, ReadWebsite, NearbyPlacesSearch]]
    messages: list = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "data": raw_image_data,
                    "media_type": "image/png",
                }
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "data": masked_image_data,
                    "media_type": "image/png",
                }
            },
            {
                "type": "text",
                "text": "Tell me about the object in the blue area surrounded by the white line."
            }
        ]
    }]

    system_prompt = f"""You are an expert in using the internet to find information about locations and objects in images. The user provides you with two images, the first image is a screenshot from their eyeballs, and the second image is almost identical to the first, except for part of the image has been masked by a blue translucent area surrounded by a white line. Your task is to provide the user with accurate information about the object in the blue area.


    If possible, start with the NearbyPlacesSearch tool. This will give you an idea of all the places of the passed type that are within 100 meters of the user's location. If you can't find the object using this tool, you can use the SearchInternet tool to search for more information about the object. If you find a website that may contain information about the object, you can use the ReadWebsite tool to extract the information from the website.

    <guidelines>
    - Only make broad assumptions about the image, and use the tools to confirm and get more details on the image.
    - You MUST consider the users current location.
    - Make sure the information is relevant to the object in the blue area, avoid detailing facts about other parts of the image.
    - Find out as much information about the object as possible, using all tools to your advantage.
    - You MUST always make a clarifying search to confirm that the object you believe that are looking at is in their current location.
    - Use as many tool use requests as required. You have no limit of the number of tool use requests.
    - If you receive a 'ValidationError' from the tool, do not give up, try to fix it and make the request again.
    - The NearbyPlacesTool is the ground truth, if the image is of a valid type of place, it will be in the NearbyPlacesTool.
    - For each fact, produce a citation to the source of the information.
    </guidelines>

    <users_current_location>{location}, lat: {lat}, lon: {lon}</users_current_location>

    First, describe only what you can directly observe in the image. Express uncertainty where necessary. Once you have a good idea of what the object is, use the tools to confirm your hypothesis. If you are unsure, ask the user for more information.
    """
    response = client.messages.create( model="claude-3-5-sonnet-latest",
            system=system_prompt,
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
                print(c.text)
            if type(c) is anthropic.types.ToolUseBlock:
                print(f"Making a tool use request to {c.name}, with input: {c.input}")
                try:
                    if c.name == "SearchInternet":
                        tool_result, cache = search(SearchInternet(**c.input), cache)
                        print(f"Response from tool: {tool_result[0:100]}")
                    elif c.name == "ReadWebsite":
                        tool_result = read(ReadWebsite(**c.input), cache)
                        print(f"Response from tool: {tool_result[0:100]}")
                    elif c.name == "NearbyPlacesSearch":
                        tool_result = nearby_places_search(NearbyPlacesSearch(**c.input), lat, lon)
                        print(f"Response from tool: {tool_result[0:100]}")
                    else:
                        print(f"Unknown tool: {c.name}")
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
                    system=system_prompt,
                    max_tokens=1024,
                    messages=messages,
                    tools=tools
            )
            messages.append({"role": "assistant", "content": response.content})


# imgs_with_locations = [("imgs/ss.png", "imgs/masked_ss.png", "Aldermanbury Square, London", 51.516, -0.093)]
# imgs_with_locations = [("imgs/dali.png", "imgs/masked_dali.png", "Vatican Museums, Vatican City", 41.903, 12.454)]
imgs_with_locations = [("imgs/church.png", "imgs/masked_church.png", "Ouro Preto, Minas Gerais",  -20.385981, -43.504831)]

for raw_img, masked_img, location, lat, lon in imgs_with_locations:
    
    print(f"Running SAM assistant on {raw_img} with location {location}")
    print("="*50)
    run_sam_assistant(raw_img, masked_img, location=location, lat=lat, lon=lon)
