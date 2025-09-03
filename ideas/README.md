## API Endpoints

### GET /location

Returns the user's current location based on their IP address.

**Response:**
```json
{
  "city": "San Francisco",
  "country": "United States",
  "latlng": [37.7749, -122.4194]
}
```

### POST /add_preference

Adds a user preference.

**Request Body:**
```json
{
  "preference": "I love Italian cuisine"
}
```

**Response:**
```json
{
  "message": "Added preference: I love Italian cuisine"
}
```

### GET /preferences

Retrieves all user preferences.

**Response:**
```json
{
  "preferences": ["I love Italian cuisine", "I enjoy outdoor activities"]
}
```

### POST /query_assistant

Queries the AI assistant for restaurant, place, or trip recommendations.

**Request Body:**
```json
{
  "id": "unique_conversation_id",
  "lat": 37.7749,
  "lon": -122.4194,
  "query_type": "restaurant",
  "query": "Suggest the top five restaurants ...",
  "stream": true
}
```

> The `query_type` accepts three values: "restaurant", "place", or "trip"

**Response:**
The response is streamed as JSON objects. Each object can be one of the following types:

1. Message:
```json
{
  "type": "message",
  "message": {
    "id": "msg_123",
    "role": "assistant",
    "content": [{"type": "text", "text": "Here are the top 5 restaurants..."}],
    "model": "claude-3-5-haiku-latest",
    "stop_reason": "end_turn"
  }
}
```

2. Message Delta (for text):
```json
{
  "type": "message_delta",
  "delta": {
    "type": "text_delta",
    "text": "Here are the top 5 restaurants..."
  }
}
```

3. Message Delta (for tool use):
```json
{
  "type": "message_delta",
  "delta": {
    "type": "tool_use",
    "id": "tool_123",
    "name": "SearchInternet",
    "input": {"query": "Top restaurants in San Francisco"}
  }
}
```

4. Error:
```json
{
  "type": "error",
  "error": {
    "type": "internal_server_error",
    "message": "An error occurred: ..."
  }
}
```

### POST /tourguide

Queries the AI tour guide for information about a specific location in an image.

**Request Body:**
```json
{
  "base_image": "base64_encoded_image",
  "masked_image": "base64_encoded_masked_image",
  "location": "San Francisco",
  "lat": 37.7749,
  "lon": -122.4194,
  "stream": true
}
```

**Response:**
The response is streamed as plain text.

### POST /sam

Sends an image and click points to the Segment Anything Model (SAM) for image segmentation.

**Request Body:**
```json
{
  "image": "base64_encoded_image",
  "clicks": [[x1, y1], [x2, y2], ...]
}
```

**Response:**
Returns the segmented image as a JPEG.

## Using the API

1. **Get User Location:**
   Send a GET request to `/location` to retrieve the user's current location.

2. **Manage User Preferences:**
   - Add preferences: Send POST requests to `/add_preference` with the user's preferences.
   - Retrieve preferences: Send a GET request to `/preferences`.

3. **Query for Recommendations:**
   Send a POST request to `/query_assistant` with `"query_type": "restaurant"`, `"query_type": "place"`, or `"query_type": "trip"` to get recommendations.

4. **Use the Tour Guide:**
   Send a POST request to `/tourguide` with an image and location information to get details about specific locations in the image.

5. **Use Image Segmentation:**
   Send a POST request to `/sam` with an image and click points to get a segmented image.

## Streamlit Demo

A Streamlit app is provided in `demo.py` to demonstrate the tool's functionality. The app allows users to:

- Enter their name
- Add and view preferences
- Choose between querying about trips, restaurants, or places
- Interact with the AI assistant through a chat interface
- Start new conversations

To run the demo:

1. Ensure all dependencies are installed `pip install -r requirements.txt`
2. Run the FastAPI server `py main.py`
3. Run the Streamlit app: `streamlit run demo.py`
