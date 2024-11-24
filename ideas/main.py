import geocoder
import streamlit as st
from anthropic.types import TextBlock, ToolUseBlock, MessageParam
import logging
from swag.assistant import convert_pydantic_to_anthropic_schema, query_claude
from swag.tools import SearchInternet, ReadWebsite, PlacesTextSearch, PlacesDetailsSearch, search, read, places_details_search, places_text_search

cache = {}

logging.basicConfig(level=logging.INFO)

g = geocoder.ip('me')
st.title("Tourism Assistant")
if "preferences" not in st.session_state:
    st.session_state.preferences = []

st.markdown(f"You are currently in **{g.city}, {g.country}**. Your location is **{g.latlng}**")
ipt = st.text_input("Tell me about yourself. I can tailor my recommendations to your preferences.")

if st.button("Add to prefrences"):
    st.session_state.preferences.append(ipt)

if st.session_state.preferences:
    st.markdown("Your preferences are:")
    for id, pref in enumerate(st.session_state.preferences):
        st.markdown(f"**{pref}**")
        delete = st.button("Delete?", key=id)
        if delete:
            st.session_state.preferences.remove(pref)

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    fr = st.button("Find restaurants?")

with col3:
    wtg = st.button("Where to go?")

if fr:
    with st.spinner("Finding restaurants..."):
        system = f"You are an AI assistant helping a user find restaurants in {g.city}, {g.country}. The user is looking for a place to eat. The user has some preferences: {"\n".join(st.session_state.preferences)}. Your goal is to build a report of the top 5 restaurants that might suit the useres preferences, including recommended menu options, expected price to eat there & overall restaurant rating. Prior to starting, detail what you plan to do in order to complete your task. You may adjust this plan as you go, reflecting on the information you find. You should update the user when you change your plan."
        messages: list[MessageParam] = [{"role": "user", "content": "Help me find a restaurant!"}]
        tools = [convert_pydantic_to_anthropic_schema(tool) for tool in [SearchInternet, ReadWebsite, PlacesDetailsSearch, PlacesTextSearch]]

        response = query_claude(messages, system, tools)
        tool_use = response.stop_reason == "tool_use"
        content = response.content
        messages.append({"role": "assistant", "content": content})

        while tool_use:
            for c in content:
                if type(c) is TextBlock:
                    st.write(c.text)
                if type(c) is ToolUseBlock:
                    st.write(f"Making a tool use request to {c.name}, with input: {c.input}")
                    if c.name == "SearchInternet":
                        tool_result, cache = search(SearchInternet(**c.input), cache) # type: ignore
                    elif c.name == "ReadWebsite":
                        tool_result = read(ReadWebsite(**c.input), cache) # type: ignore
                    elif c.name == "PlacesTextSearch":
                        tool_result = places_text_search(PlacesTextSearch(**c.input)) # type: ignore
                    elif c.name == "PlacesDetailsSearch":
                        tool_result = places_details_search(PlacesDetailsSearch(**c.input)) # type: ignore
                    else:
                        raise ValueError(f"Unknown tool: {c.name}")
                    new_input: list[dict[str, str|bool]] = [{
                        "type": "tool_result",
                        "tool_use_id": c.id,
                        "content": tool_result,
                        "is_error": False,
                    }]
                    messages.append({"role": "user", "content": new_input})
            print(messages)
            response = query_claude(messages, system, tools)
            content = response.content
            tool_use = response.stop_reason == "tool_use"
            messages.append({"role": "assistant", "content": content})
        
        if type(content[0]) is TextBlock:
            st.write(content[0].text)

if wtg:
    with st.spinner(f"Finding cool places to go in {g.city}..."):
        system = f"You are an AI assistant helping a user find places to go in {g.city}, {g.country}. The user is looking for a place to visit. The user has some preferences: {"\n".join(st.session_state.preferences)}. You may use chain of thought approaches to help the user find a place to visit. They are looking for non-restaurant locations. You should find locations based on the user's preferences."

        messages: list[MessageParam] = [{"role": "user", "content": "Help me find a place to visit!"}]
        tools = [convert_pydantic_to_anthropic_schema(tool) for tool in [SearchInternet, ReadWebsite]]

        response = query_claude(messages, system, tools)
        tool_use = response.stop_reason == "tool_use"
        content = response.content
        messages.append({"role": "assistant", "content": content})

        while tool_use:
            condensed_messages = []
            old_user = False
            for c in content:
                if type(c) is TextBlock:
                    st.write(c.text)
                if type(c) is ToolUseBlock:
                    st.write(f"Making a tool use request to {c.name}, with input: {c.input}")
                    if c.name == "SearchInternet":
                        tool_result = search(SearchInternet(**c.input))
                        print(tool_result[0:1000])
                    elif c.name == "ReadWebsite":
                        tool_result = read(ReadWebsite(**c.input))
                        print(tool_result[0:1000])
                    else:
                        raise ValueError(f"Unknown tool: {c.name}")
                    
                    new_input: list[dict[str, str|bool]] = [{
                        "type": "tool_result",
                        "tool_use_id": c.id,
                        "content": tool_result,
                        "is_error": False,
                    }]
                    messages.append({"role": "user", "content": new_input})
            response = query_claude(condensed_messages, system, tools)
            content = response.content
            tool_use = response.stop_reason == "tool_use"
            messages.append({"role": "assistant", "content": content})

        if type(content[0]) is TextBlock:
            st.write(content[0].text)
