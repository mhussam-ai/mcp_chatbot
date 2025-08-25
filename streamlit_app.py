# app.py
import streamlit as st
import asyncio
from agent_handler import (
    initialize_session_state, 
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

# --- Initialization ---
if "agent" not in st.session_state:
    initialize_session_state()

# --- Sidebar with Command Buttons ---
with st.sidebar:
    st.header("Commands")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.agent.clear_conversation_history()
        st.session_state.messages = [{"role": "assistant", "content": "History cleared. How can I help you?"}]
        st.rerun()

    if st.button("End Session and Exit", use_container_width=True, type="primary"):
        with st.spinner("Closing all sessions..."):
            run_async(close_agent_sessions(st.session_state.agent), st.session_state.loop)
        st.info("Conversation ended and all sessions closed. Refresh the page to start over.")
        st.stop()

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

            except ConnectionError as e:
                error_msg = f"Connection Error: I couldn't connect to a knowledge base. Please check the server. Details: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})