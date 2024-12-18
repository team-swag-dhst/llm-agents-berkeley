import streamlit as st
import httpx
import asyncio
import json
import uuid

st.set_page_config(
    page_title="SWAG Assistant",
    page_icon="🦛",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.title("🗺 SWAG Assistant")


def hide_streamlit_style():
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                header {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)


# Call the function to hide Streamlit style
hide_streamlit_style()


async def get_location():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/location")
        location_data = response.json()
        return location_data.get('latlng', (None, None))


# Define async functions
async def add_preference(preference):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/add_preference", json={"preference": preference}
        )
        return response.json()


async def get_preferences():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/preferences")
        return response.json()["preferences"]


async def query_assistant(query_type, query):
    lat, lon = await get_location()
    if lat is None or lon is None:
        st.error("Unable to get location. Please check your internet connection.")
        return

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/query_assistant",
            json={
                "id": str(uuid.uuid4()),
                "query_type": query_type,
                "query": query,
                "lat": lat,
                "lon": lon,
            },
            timeout=None,
        ) as response:
            async for chunk in response.aiter_text():
                yield chunk


# Sidebar for managing preferences
with st.sidebar:
    st.header("User Information")

    # Add name input
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""

    user_name = st.text_input("Enter your name:", value=st.session_state.user_name)
    if user_name:
        st.session_state.user_name = user_name
        st.success(f"Hi {user_name}!")

    st.header("User Preferences")
    new_preference = st.text_input("Add a new preference:")
    if st.button("Add Preference"):
        if new_preference:
            result = asyncio.run(add_preference(new_preference))
            st.success(f"Added preference: {new_preference}")

    st.subheader("Current Preferences:")
    preferences = asyncio.run(get_preferences())
    for pref in preferences:
        st.write(f"- {pref}")

st.write(f"Hi {user_name}! Ask about trips, restaurants, or places!")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# # Main chat interface
# st.markdown("**Choose what you want to do?**")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize query_type in session state if it doesn't exist
if "query_type" not in st.session_state:
    st.session_state.query_type = "trip"  # Default to "trip"

# Define options and their corresponding values
options = ["\U0001F500 Place", "\U0001F9ED Trip", "\U0001F32E Restaurant"]
option_values = ["place", "trip", "restaurant"]

# Radio buttons for query type selection
query_type = st.radio(
    "Choose what you want to do:",
    options,
    key="query_type_radio",
    horizontal=True,
    index=option_values.index(st.session_state.query_type),
)

# Update query_type in session state based on radio button selection
selected_value = option_values[options.index(query_type)]
if selected_value != st.session_state.query_type:
    st.session_state.query_type = selected_value
    st.rerun()  # Rerun the app to ensure consistency

# Chat input
if prompt := st.chat_input(
    f"Hi {user_name}! Ask about a {st.session_state.query_type}..."
):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Add assistant message placeholder
    with st.chat_message("assistant", avatar="🦉"):
        response_container = st.empty()
        tool_use_container = st.empty()
        error_container = st.empty()

        async def process_response():
            full_response = ""
            async for chunk in query_assistant(
                st.session_state.query_type, prompt
            ):
                try:
                    data = json.loads(chunk)
                    print(">>> DATA:", data)
                    if data["type"] == "message":
                        full_response = data["message"]["content"][0]["text"]
                        if data["message"].get("stop_reason") == "end_turn":
                            response_container.markdown(full_response)
                    elif data["type"] == "message_delta":
                        if data["delta"]["type"] == "text_delta":
                            full_response = data["delta"]["text"]
                        elif data["delta"]["type"] == "tool_use":
                            tool_use_info = f"""Tool: **{data['delta']['name']}**\n\nInput: `{json.dumps(data['delta']['input'])}`"""
                            tool_use_container.markdown(tool_use_info)
                    elif data["type"] == "error":
                        error_container.error(data["error"]["message"])
                except json.JSONDecodeError:
                    # If it's not JSON object, will ignore it
                    pass
            return full_response

        with st.spinner("Thinking..."):
            full_response = asyncio.run(process_response())

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

# Add a button to start a new conversation
if st.button("Start New Conversation"):
    st.session_state.messages = []
    st.rerun()
