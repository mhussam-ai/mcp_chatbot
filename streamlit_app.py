# app.py
import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from agent_handler import (
    initialize_agent_with_key, 
    get_agent_response, 
    close_agent_sessions
)

def run_async(coro, loop):
    """Helper function to run async code in Streamlit's sync environment."""
    return loop.run_until_complete(coro)

# --- Page Configuration ---
st.set_page_config(
    page_title="MCP Knowledge Chatbot",
    page_icon="🤖",
    layout="wide"
)
st.title("🤖 MCP Knowledge Retrieval Chatbot")

# --- Sidebar for API Key and Commands ---
with st.sidebar:
    st.header("Configuration")
    # Using type="password" hides the key as the user types it
    sidebar_api_key = st.text_input(
        "Your Google API Key",
        type="password",
        placeholder="Enter your key and press Enter",
        help="Get your API key from Google AI Studio."
    )
    
    # Check for key from all sources and store in session_state
    if sidebar_api_key:
        st.session_state.google_api_key = sidebar_api_key
    else:
        # Try to load from secrets if not entered in sidebar
        try:
            st.session_state.google_api_key = st.secrets["GOOGLE_API_KEY"]
        except (KeyError, FileNotFoundError):
            # Fallback to .env for local development
            load_dotenv()
            st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

    st.header("Commands")
    # Buttons are disabled until the agent is ready
    agent_ready = "agent" in st.session_state
    if st.button("Clear Chat History", use_container_width=True, disabled=not agent_ready):
        st.session_state.agent.clear_conversation_history()
        st.session_state.messages = [{"role": "assistant", "content": "History cleared. How can I help you?"}]
        st.rerun()

    if st.button("End Session and Exit", use_container_width=True, type="primary", disabled=not agent_ready):
        with st.spinner("Closing all sessions..."):
            run_async(close_agent_sessions(st.session_state.agent), st.session_state.loop)
        st.info("Conversation ended. Refresh to start over.")
        st.stop()

# --- Main Application Logic ---

# 1. Check if we have a key. If not, stop and wait for user input.
if not st.session_state.get("google_api_key"):
    st.info("Please enter your Google API Key in the sidebar to start the chat.")
    st.stop()

# 2. If we have a key but the agent isn't initialized, initialize it now.
if "agent" not in st.session_state:
    initialize_agent_with_key(st.session_state.google_api_key)

# 3. If we reach here, the agent is initialized and ready. Display the chat interface.
# --- Chat History Display ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input and Response Logic ---
if prompt := st.chat_input("Ask about your project needs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = run_async(
                    get_agent_response(st.session_state.agent, prompt),
                    st.session_state.loop
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})