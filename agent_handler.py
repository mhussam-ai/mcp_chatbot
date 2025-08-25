# agent_handler.py
import streamlit as st
import asyncio

from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
from prompts import AGENT_SYSTEM_PROMPT
import nest_asyncio

nest_asyncio.apply()

@st.cache_resource
def get_llm(api_key: str):
    """Returns a cached instance of the ChatGoogleGenerativeAI model."""
    return ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=api_key)

@st.cache_resource
def get_mcp_client(config_file: str):
    """Returns a cached instance of the MCPClient."""
    return MCPClient.from_config_file(config_file)

def initialize_agent_with_key(api_key: str):
    """
    Initializes the agent with a provided API key and stores it in session state.
    """
    with st.spinner("Initializing Agent... Please wait."):
        if not api_key:
            st.error("The provided API Key is empty. Cannot initialize agent.")
            st.stop()

        config_file = "config_unauth.json"
        
        # Use the provided key to get the LLM and Client
        llm = get_llm(api_key)
        client = get_mcp_client(config_file)
        
        agent = MCPAgent(
            llm=llm,
            client=client,
            memory_enabled=True,
            max_steps=20,
            system_prompt=AGENT_SYSTEM_PROMPT
        )
        
        # Store the initialized agent and other session variables
        st.session_state.agent = agent
        st.session_state.loop = asyncio.get_event_loop()
        st.session_state.messages = [{"role": "assistant", "content": "API Key accepted. How can I help you today?"}]

async def get_agent_response(agent: MCPAgent, user_prompt: str) -> str:
    """Asynchronously runs the agent and returns the complete response."""
    response = await agent.run(user_prompt)
    return response

async def close_agent_sessions(agent: MCPAgent):
    """Closes all active MCP sessions."""
    if agent and agent.client:
        await agent.client.close_all_sessions()