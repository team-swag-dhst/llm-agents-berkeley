from pydantic import BaseModel
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.build_sam import build_sam2
from pathlib import Path
import torch
import numpy as np

class SamRequest(BaseModel):
    image: bytes
    clicks: list[list[int]]

def predict_mask(request: SamRequest) -> dict:
    checkpoints_folder = Path(__file__).parent.parent / "sam2" / "checkpoints"
    checkpoint = str(checkpoints_folder / "sam2.1_hiera_tiny.pt")
    config = "configs/sam2.1/sam2.1_hiera_t.yaml"

    predictor = SAM2ImagePredictor(build_sam2(config, checkpoint))

    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        predictor.set_image(request.image)
        mask, score, logit = predictor.predict(
                point_coords = np.array(request.clicks),
                point_labels = np.array([1 for _ in range(len(request.clicks))]),
                multimask_output=False
        )

    print(mask)
    print(score)
    print(logit)

    return {
        "mask": mask
    }



with open(Path(__file__).parent.parent / "imgs" / "dali.png", "rb") as f:
    image = f.read()
    clicks = [[100, 100], [200, 200]]
    predict_mask(SamRequest(image=image, clicks=clicks))
