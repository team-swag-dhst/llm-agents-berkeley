import streamlit as st
import httpx
import asyncio
import json

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
st.title("SWAG Assistant")
st.write("Ask about trips, restaurants, or places!")

# Define async functions
async def add_preference(preference):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/add_preference",
            json={"preference": preference}
        )
        return response.json()

async def get_preferences():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/preferences")
        return response.json()["preferences"]

async def query_assistant(query_type, query):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/query_assistant",
            json={"query_type": query_type, "query": query}, timeout=None) as response: async for chunk in response.aiter_text():
                yield chunk

# Sidebar for managing preferences
with st.sidebar:
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

# Main content
query_type = st.radio("Select query type:", ["trip", "restaurant", "place"])
query = st.text_input("Enter your query:")

if 'full_response' not in st.session_state:
    st.session_state.full_response = ""

if st.button("Submit"):
    if query:
        st.session_state.full_response = ""  # Reset the response
        response_container = st.empty()
        tool_use_container = st.empty()
        error_container = st.empty()

        async def process_response():
            async for chunk in query_assistant(query_type, query):
                try:
                    data = json.loads(chunk)
                    if data['type'] == 'tool_use':
                        tool_use_info = f"""Tool: **{data['name']}**\n\nInput: `{json.dumps(data['input'])}`"""
                        tool_use_container.markdown(tool_use_info)
                    elif data['type'] == 'text':
                        if "Tool" in data['text'] and "result:" or "error" in data['text']:
                            # This is a tool result, we'll skip displaying it
                            continue
                        else:
                            # the final response
                            st.session_state.full_response = data['text']
                            response_container.markdown(st.session_state.full_response)
                    elif data['type'] == 'error':
                        error_container.error(data['text'])
                except json.JSONDecodeError:
                    # If it's not JSON object, will ignore it
                    pass

        with st.spinner("Thinking..."):
            asyncio.run(process_response())
    else:
        st.warning("Please enter a query.")
