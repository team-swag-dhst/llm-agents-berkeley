import requests
import base64

def tourguide():

    base_img_path = "imgs/dali.png"
    masked_img_path = "imgs/masked_dali.png"
    location = "Vatican Museums, Vatican City"
    lat = 41.903
    lon = 12.454

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
        "lon": lon
    }

    response = requests.post(url, json=request_body, stream=True)
    for line in response.iter_lines():
        print(line.decode("utf-8"))

def sam():

    base_img_path = "imgs/dali.png"
    with open(base_img_path, "rb") as img_file:
        base_img = img_file.read()
        base_img = base64.b64encode(base_img).decode('utf-8')

    clicks = [[100, 100], [200, 200]]
    url = "http://localhost:8000/sam"

    request_body = {
        "image": base_img,
        "clicks": clicks
    }

    response = requests.post(url, json=request_body)
    with open("response_output.png", "wb") as f:
        f.write(response.content)

tourguide()
