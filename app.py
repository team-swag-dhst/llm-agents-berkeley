from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from swag.everywhere_tour_guide import EverywhereTourGuideRequest, research_main
from swag.sam import SamRequest, predict_mask

app = FastAPI()

@app.post("/tourguide")
def everywhere_tg(request: EverywhereTourGuideRequest):
    return StreamingResponse(
        research_main(request),
        media_type="text/event-stream"
    )

@app.post("/sam")
def sam(request: SamRequest):
    return {
        "image": request.image,
        "clicks": request.clicks
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
