from pydantic import BaseModel, Field, model_validator
from urllib.parse import quote_plus
from typing import Any, Self, List, Tuple
import requests
import logging
import base64
import json
import os

from . import config as cfg
import googlemaps

from dotenv import load_dotenv
load_dotenv()

gmaps = googlemaps.Client(key=os.environ["GOOGLE_API_KEY"])

class SearchInternet(BaseModel):
    """Search the internet with the provided query. The response from this tool is a list of the search results as JSON objects containing the URL, title and a short description of the website."""

    query: str = Field(
        description="The query to search the internet with.", max_length=100
    )


class ReadWebsite(BaseModel):
    """Collect the entire content of a website given a URL. The response from this tool is a string."""

    url: str


class SearchGoogleMapsWithText(BaseModel):
    """Search google maps with the provided query. The response from this tool is a list of JSON objects containing the id, name and rating of the place."""

    query: str = Field(
        description="The query to search google maps is.", max_length=100
    )


class GetDetailsOfPlace(BaseModel):
    """Get the details of a specific place from google maps given a place id. The response from this tool is a JSON object containing the name, rating, address and price range of the place."""

    place_id: str = Field(description="The place_id of the place to get details for.")


class SearchForNearbyPlacesOfType(BaseModel):
    """Search for information of nearby places of a certain type. The range is very smalll such that the places are guaranteed to the close to the users location. The response from this tool is a list of JSON objects containing the id, name, rating of the place and a list of photos (if requested)."""

    types: list[str] = Field(
        description="The types of place to search for.", max_length=100
    )
    include_photos: bool = Field(
        description="Whether to include photos in the response.", default=False
    )
    lat: float = Field(description="The latitude of the user's location.")
    lon: float = Field(description="The longitude of the user's location.")

    @model_validator(mode="after")
    def validate_types(self) -> Self:
        for t in self.types:
            if t not in cfg.POSSIBLE_PLACE_TYPES:
                error = f"Invalid place type: {t}. Please choose from the following: {cfg.POSSIBLE_PLACE_TYPES}"
                raise ValueError(error)

        return self


class GetDirections(BaseModel):
    """Get directions between two locations."""

    origin: str = Field(description="The starting location")
    destination: str = Field(description="The destination location")
    mode: str = Field(
        description="The mode of transportation (driving, walking, bicycling, transit)",
        default="driving",
    )

class GetDistanceMatrix(BaseModel):
    """Get a matrix of distances between multiple origins and destinations."""
    origins: List[Tuple[float, float]] = Field(
        description="List of origin locations as tuples of (latitude, longitude)"
    )
    destinations: List[Tuple[float, float]] = Field(
        description="List of destination locations as tuples of (latitude, longitude)"
    )
    mode: str = Field(
        description="The mode of transportation (driving, walking, bicycling, transit)",
        default="driving",
    )

    @model_validator(mode='after')
    def check_fields(cls, values):
        for field in ['origins', 'destinations']:
            locations = values.get(field, [])
            if not locations:
                raise ValueError(f"{field.capitalize()} list cannot be empty")
            if len(locations) > 25:  # Google Maps API limit
                raise ValueError(f"Too many {field}. Maximum is 25.")
            for lat, lon in locations:
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError(f"Invalid coordinates in {field}: ({lat}, {lon})")

        # Validate mode of transport
        valid_modes = ["driving", "walking", "bicycling", "transit"]
        if values.get('mode') not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {', '.join(valid_modes)}")

        return values

class GetElevation(BaseModel):
    """Get the elevation data for a list of locations."""

    locations: list[tuple[float, float]] = Field(
        description="List of latitude/longitude pairs"
    )


class Geocode(BaseModel):
    """Convert an address to geographic coordinates or vice versa."""

    address: str = Field(description="The address to geocode")


class ReverseGeocode(BaseModel):
    """Convert geographic coordinates to an address."""

    lat: float = Field(description="Latitude")
    lng: float = Field(description="Longitude")


class GetTimeZone(BaseModel):
    """Get the time zone for a location."""

    location: tuple[float, float] = Field(description="Latitude/longitude pair")
    timestamp: int = Field(
        description="Timestamp (seconds since midnight January 1, 1970 UTC)"
    )


class GetNearestRoads(BaseModel):
    """Get the nearest roads to a set of coordinates."""

    points: list[tuple[float, float]] = Field(
        description="List of latitude/longitude pairs"
    )


class GetStaticMap(BaseModel):
    """Get a static map image."""

    center: str = Field(description="The center of the map (e.g., 'New York, NY')")
    zoom: int = Field(description="The zoom level (0-21)")
    size: str = Field(description="The size of the image in pixels (e.g., '600x400')")


class ValidateAddress(BaseModel):
    """Validate and format an address."""

    address: str = Field(description="The address to validate")


class OptimizeRoute(BaseModel):
    """Optimize the route given a distance matrix."""

    distance_matrix: List[List[float]] = Field(
        description="The distance matrix obtained from GetDistanceMatrix"
    )
    start_index: int = Field(
        description="The index of the starting point in the distance matrix", default=0
    )


class GetPhoto(BaseModel):
    """Get a photo given a name of the photo. The response is a base64 encoded image. Photo names can be obtained from the response of the SearchForNearbyPlacesOfType tool."""

    photo_name: str = Field(description="The name of the photo to get.")


class ToolRegistry:
    tools = {}

    @classmethod
    def register(cls, model):
        def decorator(func):
            cls.tools[model.__name__] = (func, model)
            return func

        return decorator

    @classmethod
    def get(cls, name):
        return cls.tools.get(name, (None, None))


@ToolRegistry.register(SearchInternet)
def search_internet(
        request: SearchInternet,
) -> str:
    url = f"https://s.jina.ai/{quote_plus(request.query)}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.environ['JINAI_API_KEY']}",
        "X-Retain-Images": "none",
    }
    response = requests.get(url, headers=headers, verify=True)
    data: list[dict[str, Any]] = response.json()["data"]

    return_value = []
    for item in data:
        _ = item.pop('content', None)
        return_value.append(item)
    
    logging.info("Received response from: `search_internet`")
    return json.dumps(return_value)


@ToolRegistry.register(ReadWebsite)
def read_website(request: ReadWebsite) -> str:

    url = f"https://r.jina.ai/{request.url}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}
    response = requests.get(url, headers=headers, verify=True)
    logging.info("Received response from: `read_website`")
    return response.text


@ToolRegistry.register(GetDetailsOfPlace)
def get_details_of_place(request: GetDetailsOfPlace) -> str:
    url = f"https://places.googleapis.com/v1/places/{request.place_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.environ["GOOGLE_API_KEY"],
        "X-Goog-FieldMask": "displayName,rating,formattedAddress,priceRange,websiteUri",
    }
    response = requests.get(url, headers=headers)
    logging.info(f"`get_details_of_place`: {response.text}")
    return json.dumps(response.json())


@ToolRegistry.register(SearchGoogleMapsWithText)
def search_google_maps_with_text(request: SearchGoogleMapsWithText) -> str:
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.environ["GOOGLE_API_KEY"],
        "X-Goog-FieldMask": "places.id,places.displayName,places.rating",
    }
    payload = {
        "textQuery": request.query,
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"`search_google_maps_with_text`: {response.text}")
    return json.dumps(response.json())


@ToolRegistry.register(SearchForNearbyPlacesOfType)
def search_for_nearby_places_of_type(
    request: SearchForNearbyPlacesOfType
) -> str:
    url = "https://places.googleapis.com/v1/places:searchNearby"
    fields = "places.id,places.displayName,places.rating"
    if request.include_photos:
        fields += ",places.photos"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.environ["GOOGLE_API_KEY"],
        "X-Goog-FieldMask": fields,
    }
    payload = {
        "includedTypes": request.types,
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {"center": {"latitude": request.lat, "longitude": request.lon}, "radius": 100}
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"`search_for_nearby_places_of_type`: {response.text}")
    return json.dumps(response.json())


@ToolRegistry.register(GetDirections)
def get_directions(request: GetDirections) -> str:
    directions = gmaps.directions(
        request.origin, request.destination, mode=request.mode
    )
    legs = directions[0]["legs"]
    logging.info(f"`get_directions`: {legs}")
    return json.dumps(legs)


@ToolRegistry.register(GetDistanceMatrix)
def get_distance_matrix(request: GetDistanceMatrix) -> str:
    try:
        matrix = gmaps.distance_matrix(
            request.origins, request.destinations, mode=request.mode.value
        )
        logging.info(f"`get_distance_matrix`: {matrix}")
        return json.dumps(matrix)
    except Exception as e:
        logging.error(f"Unexpected error in get_distance_matrix: {str(e)}")
        raise ValueError(f"Unexpected error: {str(e)}")


@ToolRegistry.register(GetElevation)
def get_elevation(request: GetElevation) -> str:
    elevation = gmaps.elevation(request.locations)
    logging.info(f"`get_elevation`: {elevation}")
    return json.dumps(elevation)


@ToolRegistry.register(Geocode)
def geocode(request: Geocode) -> str:
    geocode_result = gmaps.geocode(request.address)
    logging.info(f"`geocode`: {geocode_result}")
    coordinates = geocode_result[0]["geometry"]["location"]
    return json.dumps(coordinates)


@ToolRegistry.register(ReverseGeocode)
def reverse_geocode(request: ReverseGeocode) -> str:
    reverse_geocode_result = gmaps.reverse_geocode((request.lat, request.lng))
    logging.info(f"`reverse_geocode`: {reverse_geocode_result}")
    return json.dumps(reverse_geocode_result)


@ToolRegistry.register(GetTimeZone)
def get_time_zone(request: GetTimeZone) -> str:
    timezone = gmaps.timezone(request.location, request.timestamp)
    logging.info(f"`get_time_zone`: {timezone}")
    return json.dumps(timezone)


@ToolRegistry.register(GetNearestRoads)
def get_nearest_roads(request: GetNearestRoads) -> str:
    roads = gmaps.nearest_roads(request.points)
    logging.info(f"`get_nearest_roads`: {roads}")
    return json.dumps(roads)


@ToolRegistry.register(GetStaticMap)
def get_static_map(request: GetStaticMap) -> str:
    static_map_url = gmaps.static_map(
        center=request.center,
        zoom=request.zoom,
        size=(request.size[0], request.size[1]),
    )
    logging.info("`get_static_map`: Static map URL generated")
    return static_map_url


@ToolRegistry.register(ValidateAddress)
def validate_address(request: ValidateAddress) -> str:
    # Note: The googlemaps Python client doesn't support address validation yet
    # We'll use a placeholder implementation
    logging.warning(
        "Address validation is not supported by the googlemaps Python client. Returning input address."
    )
    return json.dumps({"input_address": request.address, "validated": False})


@ToolRegistry.register(OptimizeRoute)
def optimize_route(request: OptimizeRoute) -> str:
    distances = request.distance_matrix
    num_points = len(distances)
    unvisited = set(range(num_points))
    route = [request.start_index]
    unvisited.remove(request.start_index)
    total_distance = 0

    while unvisited:
        last = route[-1]
        next_point = min(unvisited, key=lambda x: distances[last][x])
        route.append(next_point)
        total_distance += distances[last][next_point]
        unvisited.remove(next_point)

    # Return to start
    route.append(request.start_index)
    total_distance += distances[route[-2]][request.start_index]

    result = {"optimized_route": route, "total_distance": total_distance}

    logging.info(f"`optimize_route`: {result}")
    return json.dumps(result)


@ToolRegistry.register(GetPhoto)
def get_photo(request: GetPhoto) -> str:
    url = f"https://places.googleapis.com/v1/{request.photo_name}/media?maxHeightPx=400&maxWidthPx=400&key={os.environ['GOOGLE_API_KEY']}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    base64_image = base64.b64encode(response.content).decode("utf-8")
    return base64_image
