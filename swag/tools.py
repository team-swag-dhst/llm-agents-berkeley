from pydantic import BaseModel, Field, model_validator
import requests
from urllib.parse import quote_plus
import os
import logging
import json
from typing import Any, Self
from . import config as cfg
import base64

from dotenv import load_dotenv
load_dotenv()

class SearchInternet(BaseModel):
    """Search the internet with the provided query. The response from this tool is a list of the search results as JSON objects containing the URL, title and a short description of the website."""
    query: str = Field(description="The query to search the internet with.", max_length=100)

class ReadWebsite(BaseModel):
    """Collect the entire content of a website given a URL. The response from this tool is a string."""
    url: str

class SearchGoogleMapsWithText(BaseModel):
    """Search google maps with the provided query. The response from this tool is a list of JSON objects containing the id, name and rating of the place.""" 
    query: str = Field(description="The query to search google maps is.", max_length=100)

class GetDetailsOfPlace(BaseModel):
    """Get the details of a specific place from google maps given a place id. The response from this tool is a JSON object containing the name, rating, address and price range of the place."""
    place_id: str = Field(description="The place_id of the place to get details for.")

class SearchForNearbyPlacesOfType(BaseModel):
    """Search for information of nearby places of a certain type. The range is very smalll such that the places are guaranteed to the close to the users location. The response from this tool is a list of JSON objects containing the id, name, rating of the place and a list of photos (if requested)."""
    types: list[str] = Field(description="The types of place to search for.", max_length=100)
    include_photos: bool = Field(description="Whether to include photos in the response.", default=False)

    @model_validator(mode='after')
    def validate_types(self) -> Self:
        for t in self.types:
            if t not in cfg.POSSIBLE_PLACE_TYPES:
                error = f"Invalid place type: {t}. Please choose from the following: {cfg.POSSIBLE_PLACE_TYPES}"
                raise ValueError(error)

        return self

class GetPhoto(BaseModel):
    """Get a photo given a name of the photo. The response is a base64 encoded image. Photo names can be obtained from the response of the SearchForNearbyPlacesOfType tool."""
    photo_name: str = Field(description="The name of the photo to get.")


def search_internet(request: SearchInternet, cache: dict[str, str]) -> tuple[str, dict]:
    url = f"https://s.jina.ai/{quote_plus(request.query)}"
    headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['JINAI_API_KEY']}",
            "X-Retain-Images": "none",
            "X-With-Generated-Alt": "true"
    }
    response = requests.get(url, headers=headers)
    data: list[dict[str, Any]] = response.json()['data']

    return_value = []
    for item in data:
        content = item.pop('content', None)
        if len(content) > 0:
            cache[item['url']] = content 
        return_value.append(item)

    logging.info(f"`search_internet`: {return_value}")
    return json.dumps(return_value), cache

def read_website(request: ReadWebsite, cache: dict[str, str]) -> str:
    if request.url in cache:
        return cache[request.url]

    url = f"https://r.jina.ai/{request.url}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}
    response = requests.get(url, headers=headers)
    logging.info(f"`read_website` (truncated): {response.text[:1000]}")
    return response.text

def get_details_of_place(request: GetDetailsOfPlace) -> str:
    url = f"https://places.googleapis.com/v1/places/{request.place_id}"
    headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": os.environ['GOOGLE_API_KEY'],
            "X-Goog-FieldMask": "displayName,rating,formattedAddress,priceRange,websiteUri"
    }
    response = requests.get(url, headers=headers)
    logging.info(f"`get_details_of_place`: {response.text}")
    return json.dumps(response.json())

def search_google_maps_with_text(request: SearchGoogleMapsWithText) -> str:
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": os.environ['GOOGLE_API_KEY'],
            "X-Goog-FieldMask": "places.id,places.displayName,places.rating"
    }
    payload = {
        "textQuery": request.query,
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"`search_google_maps_with_text`: {response.text}")
    return json.dumps(response.json())

def search_for_nearby_places_of_type(request: SearchForNearbyPlacesOfType, lat: float, lon: float) -> str:
    url = "https://places.googleapis.com/v1/places:searchNearby"
    fields = "places.id,places.displayName,places.rating"
    if request.include_photos:
        fields += ",places.photos"
    headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": os.environ['GOOGLE_API_KEY'],
            "X-Goog-FieldMask": fields
    }
    payload = {
        "includedTypes": request.types,
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": 100
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"`search_for_nearby_places_of_type`: {response.text}")
    return json.dumps(response.json())

def get_photo(request: GetPhoto) -> str:
    url = f"https://places.googleapis.com/v1/{request.photo_name}/media?maxHeightPx=400&maxWidthPx=400&key={os.environ['GOOGLE_API_KEY']}"
    headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    base64_image = base64.b64encode(response.content).decode('utf-8')
    return base64_image
