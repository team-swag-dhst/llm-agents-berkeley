# main.py
import sys
import os
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from anthropic import AsyncAnthropic
from pydantic import BaseModel
import geocoder

from swag.tools import (
    SearchInternet,
    ReadWebsite,
    SearchForNearbyPlacesOfType,
    Geocode,
    GetDistanceMatrix,
    OptimizeRoute,
)
from swag.assistant import Assistant

app = FastAPI()

assistant = Assistant(
    client=AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY")),
    model="claude-3-5-haiku-latest",
)


class UserPreference(BaseModel):
    preference: str


class Query(BaseModel):
    query_type: str  # 'restaurant' or 'place' or 'trip'
    query: str


# In-memory storage for preferences (might be replaced with a database later)
user_preferences: List[str] = []


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


@app.post("/query_assistant")
async def query_assistant(
    query: Query, preferences: List[str] = Depends(get_preferences)
):
    g = geocoder.ip("me")
    preferences_str = ", ".join(user_preferences)
    location_str = f"{g.city}, {g.country}"

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
                action=action
            )
            assistant.define_tools([SearchInternet, ReadWebsite, SearchForNearbyPlacesOfType])
        else:
            yield f"Invalid query type: {query.query_type}. Supported types are 'restaurant', 'place', and 'trip'."
            return

        # Use async for to iterate over the assistant's response
        async for response_chunk in assistant(query.query):
            yield response_chunk

    return StreamingResponse(generate_response(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
