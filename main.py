# main.py
import sys
import os
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from anthropic import AsyncAnthropic
from pydantic import BaseModel, ConfigDict
from io import BytesIO
import geocoder
import uuid

from swag.tools import (
    SearchInternet,
    ReadWebsite,
    SearchForNearbyPlacesOfType,
    Geocode,
    ReverseGeocode,
    GetDistanceMatrix,
    OptimizeRoute,
    reverse_geocode
)
from swag.assistant import Assistant
from swag.sam import predict_mask
from swag.everywhere_tour_guide import run_everywhere_tour_guide
import logging


logging.basicConfig(level=logging.INFO)

import logging


logging.basicConfig(level=logging.INFO)

app = FastAPI()

origins = ["*"]
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)

class SamRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image: str
    clicks: list[list[int]]

class TourGuideRequest(BaseModel):
    base_image: str
    masked_image: str
    location: str
    lat: float
    lon: float
    stream: bool = True

class UserPreference(BaseModel):
    preference: str

class Query(BaseModel):
    id: str
    lat: float
    lon: float
    query_type: str  # 'restaurant' or 'place' or 'trip'
    query: str
    stream: bool = True


# In-memory storage for preferences (might be replaced with a database later)
user_preferences: List[str] = []
conversations = {}


@app.get("/location")
async def get_location():
    g = geocoder.ip("me")
    return {"city": g.city, "country": g.country, "latlng": g.latlng}


@app.post("/add_preference")
async def add_preference(preference: UserPreference):
    user_preferences.append(preference.preference)
    return {"message": f"Added preference: {preference.preference}"}


@app.get("/preferences")
async def get_preferences():
    return {"preferences": user_preferences}

@app.post("/tourguide")
async def query_everywhere_tourguide(
        request: TourGuideRequest, location: dict[str, str] = Depends(get_location)
):
    if not request.location:
        request.location = reverse_geocode(ReverseGeocode(lat=request.lat, lng=request.lon))

    request.base_image = request.base_image.replace("data:image/jpeg;base64,", "")
    request.masked_image = request.masked_image.replace("data:image/jpeg;base64,", "")

    if request.stream:   
        return StreamingResponse(
                run_everywhere_tour_guide(
                    request.base_image,
                    request.masked_image,
                    request.location,
                    request.lat,
                    request.lon
                ),
                media_type="text/plain"
        )

    response = "".join([chunk async for chunk in run_everywhere_tour_guide(request.base_image, request.masked_image, request.location, request.lat, request.lon)])
    return response


@app.post("/query_assistant")
async def query_assistant(
    query: Query, preferences: dict[str, list[str]] = Depends(get_preferences)
):

    previous_conversation = conversations.get(query.id, [])

    assistant = Assistant(
        client=AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY")),
        model="claude-3-5-haiku-latest",
    )

    assistant.messages = previous_conversation
    user_preferences = preferences["preferences"]
    preferences_str = ", ".join(user_preferences)
    location_str = reverse_geocode(ReverseGeocode(lat=query.lat, lng=query.lon))

    async def generate_response():
        if query.query_type == "trip":
            system_trip = """
            You are an AI trip planner.
            The user wants to travel, given a set of places and waypoints.

            Your goal is to create a detailed trip plan including:
            1. Route information (directions, distances, estimated travel times).
            2. Suggested activities and attractions along the route and at the destination.
            3. Potential accommodation options at the destination.
            4. Any relevant warnings or advisories for the trip (e.g., road closures, weather).

            Use tools to gather the necessary information. Provide the plan.
            """
            assistant.system = system_trip
            assistant.define_tools(
                [SearchInternet, ReadWebsite, Geocode, GetDistanceMatrix, OptimizeRoute]
            )
        elif query.query_type in ["restaurant", "place"]:
            system_template = """
            You are an AI assistant helping a user find {query_type}s in {location}.
            The user is looking for a {query_type} to {action}.
            The user's preferences are: {preferences_str}.
            Your goal is to build a report of the top 5 {query_type}s that might suit the user's preferences,
            including {additional_info}."""

            additional_info = (
                "recommended menu options, expected price to eat there & overall restaurant rating"
                if query.query_type == "restaurant"
                else "recommended activities, expected costs & overall ratings"
            )

            action = "eat" if query.query_type == "restaurant" else "visit"

            assistant.system = system_template.format(
                query_type=query.query_type,
                location=location_str,
                preferences_str=preferences_str,
                additional_info=additional_info,
                action=action)
            assistant.define_tools([SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType])
        else:
            yield f"Invalid query type: {query.query_type}. Supported types are 'restaurant', 'place', and 'trip'."
            return
        
        # Use async for to iterate over the assistant's response
        async for response_chunk in assistant(query.query):
            conversations[query.id] = assistant.messages
            yield response_chunk
    
    if query.stream:
        return StreamingResponse(generate_response(), media_type="text/plain")
    else:
        return "".join([chunk async for chunk in generate_response()])

@app.post("/sam")
async def sam(request: SamRequest):
    request.image = request.image.replace("data:image/jpeg;base64,", "")
    image = predict_mask(request.image, request.clicks)
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return Response(
        content=img_byte_arr,
        media_type="image/jpeg"
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
