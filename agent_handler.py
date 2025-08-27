# agent_handler.py
import streamlit as st
import os
import asyncio
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from prompts import AGENT_SYSTEM_PROMPT
import nest_asyncio
import asyncio

nest_asyncio.apply()

@st.cache_resource
def get_llm(api_key: str):
    """Returns a cached instance of the ChatGoogleGenerativeAI model."""
    return ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=SecretStr(api_key))

@st.cache_resource
def get_mcp_client(config_file: str):
    """Returns a cached instance of the MCPClient."""
    return MCPClient.from_config_file(config_file)

def initialize_session_state():
    """
    Initializes the agent, its dependencies, and stores them in the session state.
    This function is called only once per session.
    """
    with st.spinner("Initializing Agent... Please wait."):
        # Use Streamlit secrets for deployment, with a .env fallback for local dev
        try:
            GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        except (FileNotFoundError, KeyError):
            load_dotenv()
            GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

        if not GOOGLE_API_KEY:
            st.error("Google API Key not found. Please set it in Streamlit secrets or a .env file.")
            st.stop()

        config_file = "config.json"
        
        llm = get_llm(GOOGLE_API_KEY)
        client = get_mcp_client(config_file)
        
        agent = MCPAgent(
            llm=llm,
            client=client,
            memory_enabled=True,
            max_steps=20,
            system_prompt=AGENT_SYSTEM_PROMPT # Use the imported prompt
        )
        
        st.session_state.agent = agent
        st.session_state.loop = asyncio.get_event_loop()
        st.session_state.cleanup_event = asyncio.Event()
        st.session_state.cleanup_task = st.session_state.loop.create_task(
            _run_cleanup_task(agent, st.session_state.cleanup_event)
        )
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you today?"}]

async def _run_cleanup_task(agent: MCPAgent, cleanup_event: asyncio.Event):
    """Long-running task to handle agent cleanup when the event is set."""
    await cleanup_event.wait()
    if agent and agent.client:
        await agent.client.close_all_sessions()

async def get_agent_response(agent: MCPAgent, user_prompt: str) -> str:
    """Asynchronously runs the agent and returns the complete response."""
    response = await agent.run(user_prompt)
    return response

async def close_agent_sessions(cleanup_event: asyncio.Event, cleanup_task: asyncio.Task):
    """Triggers and awaits the cleanup task."""
    cleanup_event.set()
    await cleanup_task
