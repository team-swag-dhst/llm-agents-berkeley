import requests
import base64

base_img_path = "imgs/dali.png"
masked_img_path = "imgs/masked_dali.png"
location = "Vatican Museums, Vatican City"
lat = 41.903
lon = 12.454

with open(base_img_path, "rb") as img_file:
    base_img = base64.b64encode(img_file.read()).decode("utf-8")

with open(masked_img_path, "rb") as img_file:
    masked_img = base64.b64encode(img_file.read()).decode("utf-8")

url = "http://localhost:8080/tourguide"

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

