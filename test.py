import requests
import base64


def tourguide():
    base_img_path = "imgs/dali.jpg"
    masked_img_path = "imgs/masked_dali.jpg"
    location = "Vatican Museum"
    lat = 41.906314680189425
    lon = 12.454854851168495

    with open(base_img_path, "rb") as img_file:
        base_img = base64.b64encode(img_file.read()).decode("utf-8")

    with open(masked_img_path, "rb") as img_file:
        masked_img = base64.b64encode(img_file.read()).decode("utf-8")

    url = "http://localhost:8000/tourguide"

    request_body = {
        "base_image": base_img,
        "masked_image": masked_img,
        "location": location,
        "lat": lat,
        "lon": lon,
        "stream": True,
    }

    # Using requests for streaming
    with requests.post(url, json=request_body, stream=True) as response:
        if response.status_code == 200:
            for chunk in response.iter_content(
                chunk_size=1024
            ):  # Adjust chunk_size as needed
                if chunk:  # filter out keep-alive new chunks
                    print(chunk.decode("utf-8"), end="\n\n")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    print()


def sam():
    base_img_path = "imgs/dali.png"
    with open(base_img_path, "rb") as img_file:
        base_img = base64.b64encode(img_file.read()).decode("utf-8")

    clicks = [[100, 100], [200, 200]]
    url = "http://localhost:8000/sam"

    request_body = {"image": base_img, "clicks": clicks}

    # Using requests for non-streaming
    response = requests.post(url, json=request_body)
    if response.status_code == 200:
        with open("response_output.png", "wb") as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


tourguide()
# sam() # Uncomment to test the sam function
