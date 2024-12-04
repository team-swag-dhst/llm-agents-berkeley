from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.build_sam import build_sam2
from pathlib import Path
import cv2
import torch
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
import os
import base64

checkpoint = os.environ["HOME"] + "/sam2/checkpoints/sam2.1_hiera_tiny.pt"
config = "configs/sam2.1/sam2.1_hiera_t.yaml"

predictor = SAM2ImagePredictor(build_sam2(config, checkpoint))

def predict_mask(og_image: str, clicks: list[list[int]]) -> Image.Image:
    image_bytes = base64.b64decode(og_image)
    pil_img = Image.open(BytesIO(image_bytes))
    img = np.array(pil_img.convert("RGB"))

    point_coords = np.array(clicks)
    point_labels = np.array([1 for _ in range(len(clicks))])

    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        predictor.set_image(img)
        masks, scores, logits = predictor.predict(
                point_coords = point_coords,
                point_labels = point_labels,
                multimask_output=True
        )


    sorted_ind = np.argsort(scores)[-1]
    mask = masks[sorted_ind]
    # score = scores[sorted_ind]
    # logit = logits[sorted_ind]


    color = np.array([30/255, 144/255, 255/255, 0.5])
    h, w = mask.shape[-2:]
    mask = mask.astype(np.uint8)
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cv2.approxPolyDP(contour, epsilon=0.01, closed=True) for contour in contours]
    mask_image = cv2.drawContours(mask_image, contours, -1, (1, 1, 1, 1.0), thickness=10)

    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')

    mask_pil = Image.fromarray((mask_image * 255).astype(np.uint8), 'RGBA')

    result = Image.alpha_composite(pil_img, mask_pil)

    if point_coords is not None and point_labels is not None:
        draw = ImageDraw.Draw(result)

        radius = 10
        for coord, label in zip(point_coords, point_labels):
            x, y = coord
            color = 'green' if label == 1 else 'red'
            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                        fill=color)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                        outline='white', width=2)

    return result

# image_path = Path(__file__).parent.parent / "imgs" / "dali.png"
# with open(image_path, "rb") as f:
#     image = f.read()
#     image = base64.b64encode(image).decode('utf-8')
# 
# clicks = [[100, 100], [200, 200]]
# predict_mask(image, clicks)
