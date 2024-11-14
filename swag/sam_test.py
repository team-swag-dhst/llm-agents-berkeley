import base64
import anthropic
from .tools import SearchInternet, search, ReadWebsite, read
from .assistant import convert_pydantic_to_anthropic_schema
import os
from dotenv import load_dotenv

load_dotenv()

def condense_messages(messages: list) -> list:

    condensed_messages = []
    last_message = messages[-1]
    for message in messages[:-1]:
        if message["role"] == "assistant":
            condensed_messages.append(message)
        else:
            old_content = message["content"]
            if old_content[0]["type"] == "tool_result":
                new_content = {
                    "type": old_content[0]["type"],
                    "tool_use_id": old_content[0]["tool_use_id"],
                    "content": old_content[0]["content"][0:500],
                    "is_error": old_content[0]["is_error"],
                }
                condensed_messages.append({"role": "user", "content": [new_content]})
            else:
                condensed_messages.append(message)
    
    condensed_messages.append(last_message)
    return condensed_messages

def run_sam_assistant(img_path: str, location: str):
    with open(img_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    tools: list = [convert_pydantic_to_anthropic_schema(tool) for tool in [SearchInternet, ReadWebsite]]
    messages: list = [{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "data": image_data,
                    "media_type": "image/png",
                }
            },
            {
                "type": "text",
                "text": "Tell me about the object in the blue area."
            }
        ]
    }]

    system_prompt = f"""You are a research assistant that can help a user with researching what they are currently looking at. The user has provided an image of an object that they are interested in. They are interested in a specific section of the image, which has been marked with a star and a blue translucent area. Your task is to research the specific object in the blue area and detail this to the user. You will be given the current location of the user to help guide your queries.

    <guidelines>
    - The fact that the image has a star and is blue is irrelevant, research the object in the blue area.
    - Make sure the information is relevant to the object in the blue area, try to avoid detailing facts about other parts of the image.
    - Make multiple queries if necessary to confirm the information.
    - Consider the users current location, as they are currently looking at the object.
    - Once you have gathered enough information, make a clarifying search to confirm the object you believe it is is in the correct location.
    </guidelines>

    <users_current_location>{location}</users_current_location>
    """
    response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            system=system_prompt,
            max_tokens=1024,
            messages=messages,
            tools=tools
    )
    tool_use = response.stop_reason == "tool_use"
    messages.append({"role": "assistant", "content": response.content})

    while tool_use:
        messages = condense_messages(messages)
        tool_use = response.stop_reason == "tool_use"
        for c in response.content:
            if type(c) is anthropic.types.TextBlock:
                print(c.text)
            if type(c) is anthropic.types.ToolUseBlock:
                print(f"Making a tool use request to {c.name}, with input: {c.input}")
                if c.name == "SearchInternet":
                    tool_result = search(SearchInternet(**c.input))
                    print(f"Response from tool: {tool_result[0:100]}")
                elif c.name == "ReadWebsite":
                    tool_result = read(ReadWebsite(**c.input))
                    print(f"Response from tool: {tool_result[0:100]}")
                else:
                    raise ValueError(f"Unknown tool: {c.name}")
                new_input = [{
                    "type": "tool_result",
                    "tool_use_id": c.id,
                    "content": tool_result,
                    "is_error": False,
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


imgs_with_locations = [("imgs/masked_ss.png", "Aldermanbury Square, London")]# ("imgs/masked_tf.png", "Centro Storico, Rome")]
for img, location in imgs_with_locations:
    print(f"Running SAM assistant on {img} with location {location}")
    print("="*50)
    run_sam_assistant(img, location)
