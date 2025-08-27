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

# --- Header and Welcome Message ---
st.title("🤖 MCP Knowledge Retrieval Chatbot")
st.info("Welcome! I'm your AI assistant for retrieving information about your project needs. Ask me anything about your project, and I'll do my best to provide relevant information from the connected knowledge bases.")

# --- Initialization ---
if "agent" not in st.session_state:
    initialize_session_state()
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}] # Initial message for new sessions

# --- Sidebar with Command Buttons and About Section ---
with st.sidebar:
    st.image("logo-white-2-scaled.png", width="stretch", caption="DataToBiz")
    st.header("Commands")
    if st.button("Clear Chat History", width="stretch"):
        st.session_state.agent.clear_conversation_history()
        st.session_state.messages = [{"role": "assistant", "content": "History cleared. How can I help you?"}]
        st.rerun()

    if st.button("End Session and Exit", width="stretch", type="primary"):
        with st.spinner("Closing all sessions..."):
            run_async(
                close_agent_sessions(st.session_state.cleanup_event, st.session_state.cleanup_task),
                st.session_state.loop
            )
        st.error("Conversation ended and all sessions closed. Refresh the page to start over.") # st.error for more prominence
        st.stop()

    st.markdown("---")
    st.header("About")
    st.markdown(
        """
        This chatbot leverages the Model Context Protocol (MCP) to retrieve knowledge from various sources.
        It's designed to assist you with project-specific queries by connecting to relevant MCP servers.
        """
    )

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
                st.exception(e) # Using st.exception for detailed error display
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                st.exception(e) # Using st.exception for detailed error display
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
