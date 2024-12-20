# main.py
import sys
import os
from typing import List, Dict
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from pydantic import BaseModel, ConfigDict
from io import BytesIO
import geocoder
import json

from swag.tools import (
    SearchInternet,
    ReadWebsite,
    SearchForNearbyPlacesOfType,
    Geocode,
    ReverseGeocode,
    GetDistanceMatrix,
    OptimizeRoute,
    reverse_geocode,
)
from swag.assistant import Assistant

from swag.sam import predict_mask
from swag.everywhere_tour_guide import run_everywhere_tour_guide
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CORS ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model and Client ---
# model_id = "claude-3-5-sonnet-latest"
model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
client = anthropic.AsyncAnthropicBedrock()


# --- Pydantic Models ---
class SamRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image: str
    clicks: list[list[int]]


class TourGuideRequest(BaseModel):
    base_image: str
    masked_image: str = ""
    location: str = ""
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


# --- In-memory storage for preferences (consider a database for production) ---
user_preferences: List[str] = []

# --- In-memory conversation storage with expiration ---
conversations: Dict[str, Dict] = {}
# {conversation_id: {"messages": [], "last_updated": datetime}}
CONVERSATION_TIMEOUT = timedelta(minutes=30)
# Expire conversations after 30 minutes of inactivity


def cleanup_conversations():
    now = datetime.now()
    expired_ids = [
        conversation_id
        for conversation_id, data in conversations.items()
        if now - data["last_updated"] > CONVERSATION_TIMEOUT
    ]
    print(">> Number of expired messages:", len(expired_ids))
    for conversation_id in expired_ids:
        del conversations[conversation_id]
    print(">> # Total messages: ", len(conversations))
    print(">> Total messages: ", conversations)


# --- Routes ---
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
        request.location = reverse_geocode(
            ReverseGeocode(lat=request.lat, lng=request.lon)
        )

    # Ensure images are base64 strings without the data URL prefix
    request.base_image = request.base_image.replace("data:image/jpeg;base64,", "")
    request.masked_image = request.masked_image.replace("data:image/jpeg;base64,", "")

    if request.stream:
        return StreamingResponse(
            run_everywhere_tour_guide(
                base_image=request.base_image,
                masked_image=request.masked_image,
                location=request.location,
                lat=request.lat,
                lon=request.lon,
            ),
            media_type="text/plain",
        )

    response = "".join(
        [
            chunk
            async for chunk in run_everywhere_tour_guide(
                base_image=request.base_image,
                masked_image=request.masked_image,
                location=request.location,
                lat=request.lat,
                lon=request.lon,
            )
        ]
    )
    return response


@app.post("/query_assistant")
async def query_assistant(
    query: Query,
    preferences: dict[str, list[str]] = Depends(get_preferences),
):
    cleanup_conversations()  # Clean up expired conversations before each request

    # Use the query.id as the conversation ID
    conversation_id = query.id

    # Initialize conversation data if it doesn't exist
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "messages": [],
            "last_updated": datetime.now(),
        }

    # Create a new Assistant instance for each request
    swag_assistant = Assistant(
        client=client,
        model=model_id,
    )

    # Load messages into the assistant
    swag_assistant.messages = conversations[conversation_id]["messages"]
    print(">> PREVIOUS MESSAGES:", swag_assistant.messages)

    user_preferences = preferences["preferences"]
    preferences_str = ", ".join(user_preferences)
    location_str = reverse_geocode(ReverseGeocode(lat=query.lat, lng=query.lon))

    async def generate_response():
        if query.query_type == "trip":
            system_trip = """
            You are an AI trip planner designed to create personalized travel itineraries. When a user provides their travel destinations and preferences, your task is to:

            1. Outline a high-level route between the given locations, including major waypoints.
            2. Suggest 2-3 key activities or attractions for each location, tailored to the user's interests if provided.
            3. Recommend a suitable accommodation type for the destination (e.g., hotel, hostel, vacation rental).
            4. Highlight any crucial travel advisories or potential issues (weather, road conditions, local events).

            Prioritize brevity and relevance over exhaustive details. Use available tools to gather accurate, up-to-date information. Present the plan in a clear, concise format that's easy for the user to understand and act upon. Be prepared to adjust the plan based on user feedback or questions.

            Note: if you need to geocode, use internet search of geolocation, not the geocode tool
            """
            swag_assistant.system = system_trip
            swag_assistant.define_tools(
                [
                    SearchInternet,
                    ReadWebsite,
                    GetDistanceMatrix,
                    OptimizeRoute,
                    Geocode,
                ]
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

            swag_assistant.system = system_template.format(
                query_type=query.query_type,
                location=location_str,
                preferences_str=preferences_str,
                additional_info=additional_info,
                action=action,
            )
            swag_assistant.define_tools(
                [SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType]
            )
        else:
            yield json.dumps(
                {
                    "type": "error",
                    "text": f"Invalid query type: {query.query_type}. Supported types are 'restaurant', 'place', and 'trip'.",
                }
            )
            return

        async for response_chunk in swag_assistant(query.query):
            conversations[conversation_id]["messages"] = (
                swag_assistant.messages.copy()
            )
            conversations[conversation_id]["last_updated"] = datetime.now()
            logger.info(">>> Response Chunk: %s", response_chunk)
            yield json.dumps(response_chunk)

    if query.stream:
        return StreamingResponse(generate_response(), media_type="text/plain")
    else:
        return "".join([chunk async for chunk in generate_response()])


@app.post("/sam")
async def sam(request: SamRequest):
    request.image = request.image.replace("data:image/jpeg;base64,", "")
    image = predict_mask(request.image, request.clicks)
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()
    return Response(content=img_byte_arr, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
