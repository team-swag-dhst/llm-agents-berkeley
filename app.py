from fastapi import FastAPI
from fastapi.responses import StreamingResponse, Response
import uvicorn
from swag.everywhere_tour_guide import EverywhereTourGuideRequest, research_main
from swag.sam import SamRequest, predict_mask
from io import BytesIO

app = FastAPI()

@app.post("/tourguide")
def everywhere_tg(request: EverywhereTourGuideRequest):
    return StreamingResponse(
        research_main(request),
        media_type="text/event-stream"
    )

@app.post("/sam")
def sam(request: SamRequest):

    image = predict_mask(request)
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    image.save("output.png")

    return Response(
        content=img_byte_arr,
        media_type="image/png"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
