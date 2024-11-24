from pydantic import BaseModel

class EverywhereTourGuideRequest(BaseModel):
    base_image: str
    masked_image: str
    location: str
    lat: float
    lon: float

def research_main(request: EverywhereTourGuideRequest):
    pass
    

