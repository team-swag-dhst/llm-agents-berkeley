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

### POST /query_assistant

Queries the AI assistant for restaurant or place recommendations.

**Request Body:**
```json
{
  "query_type": "restaurant",
  "query": "Suggest the top five restaurants ..."
}
```

> the query_type accepts three values: "restaurant", "place" or "trip"

**Response:**
```json
{
  "response": "Here are the top 5 restaurants that might suit your preferences..."
}
```

## Using the API

1. **Get User Location:**
   Send a GET request to `/location` to retrieve the user's current location.

2. **Add User Preferences:**
   Send POST requests to `/add_preference` with the user's preferences. You can add multiple preferences by sending multiple requests.

3. **Query for Recommendations:**
   Send a POST request to `/query_assistant` with either `"query_type": "restaurant"`, `"query_type": "place"`, or `"query_type": "trip"` to get recommendations.


> We attached a [Streamlit app](../ideas/demo.py) to demonstrate the tool use.
