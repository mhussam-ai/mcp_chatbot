# Knowledge Transfer Document: MCP Chatbot

## 1. Introduction

This document provides a comprehensive overview of the MCP Chatbot codebase. The MCP Chatbot is a Streamlit-based application designed to act as an AI assistant for knowledge retrieval. It leverages the Model Context Protocol (MCP) to connect to various knowledge sources (e.g., Notion, Google Drive via n8n) and uses a Google Generative AI model (Gemini-2.5-flash) to process user queries and retrieve relevant information. Its primary mission is to accelerate the creation of client-facing documents by finding relevant internal resources.

## 2. Project Structure

The project consists of the following key files:

*   `config.json`: Configuration file for MCP servers.
*   `requirements.txt`: Lists all Python dependencies required for the project.
*   `prompts.py`: Contains the system prompt that guides the AI agent's behavior.
*   `agent_handler.py`: Manages the initialization and interaction with the AI agent and MCP client.
*   `streamlit_app.py`: The main Streamlit application file, handling the user interface and orchestrating the chatbot's flow.
*   `.env`: Used for local development to store environment variables like API keys.
*   `.gitignore`: Specifies intentionally untracked files to ignore.
*   `README.md`: Project README file.
*   `logo-white-2-scaled.png`: Logo image used in the Streamlit app.

## 3. Dependencies (`packages.txt`, `requirements.txt`)

The following packages are essential for the project:

- packages.txt
*   `Python >=3.13`
*   `Node.js >=18` : for the `npx mcp-remote` commands to work.

- requirements.txt
*   `streamlit`: For building interactive web applications.
*   `langchain`: A framework for developing applications powered by language models.
*   `langchain-google-genai`: Integrates Google's Generative AI models with Langchain.
*   `google-generativeai`: Google's official client library for Generative AI.
*   `python-dotenv`: For loading environment variables from a `.env` file.
*   `mcp_use`: The library for interacting with Model Context Protocol (MCP) servers.
*   `nest_asyncio`: Allows nested use of `asyncio.run` and `loop.run_until_complete`.

## 4. MCP Configuration (`config.json`)

The `config.json` file defines the MCP servers that the chatbot can connect to. Each entry specifies a server name and the command/arguments to launch it.

```json
{
  "mcpServers": {
    "notionMCP": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.notion.com/mcp" // official Notion MCP Server
      ]
    },
    "n8n": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://jayef.app.n8n.cloud/mcp/vector-datatobiz" // our custom Gdrive server hosted at n8n
      ]
    }
  }
}
```

*   **`notionMCP`**: Connects to a Notion workspace via an Official Notion MCP Remote server.
*   **`gdrive`**: Connects to an n8n MCP instance, which in turn provides access to our Custom Google Drive MCP (e.g., for searching and reading files).

## 5. Agent Logic (`agent_handler.py`)

This file contains the core logic for initializing and managing the AI agent.

*   **`get_llm(api_key: str)`**:
    *   A Streamlit cached resource function that initializes and returns a `ChatGoogleGenerativeAI` model instance.
    *   Uses `gemini-2.5-flash` as the language model.
    *   The Google API key is passed as a `SecretStr` for security.
*   **`get_mcp_client(config_file: str)`**:
    *   A Streamlit cached resource function that initializes and returns an `MCPClient` instance.
    *   It loads MCP server configurations from the specified `config_file` (e.g., `config.json`).
*   **`initialize_session_state()`**:
    *   This function is called once per Streamlit session to set up the agent and its dependencies.
    *   It retrieves the `GOOGLE_API_KEY` from Streamlit secrets (for deployment) or a `.env` file (for local development).
    *   Initializes the `ChatGoogleGenerativeAI` LLM and `MCPClient`.
    *   Creates an `MCPAgent` instance, configuring it with the LLM, MCP client, memory, max steps, and the `AGENT_SYSTEM_PROMPT`.
    *   Sets up an `asyncio` event loop and a cleanup task to ensure MCP sessions are properly closed when the Streamlit session ends.
    *   Initializes the chat `messages` in `st.session_state`.
*   **`_run_cleanup_task(agent: MCPAgent, cleanup_event: asyncio.Event)`**:
    *   An asynchronous task that waits for a `cleanup_event` to be set.
    *   Once triggered, it closes all active MCP client sessions, ensuring resources are released. (Currently Not working as Intended)
*   **`get_agent_response(agent: MCPAgent, user_prompt: str) -> str`**:
    *   An asynchronous function that takes the `MCPAgent` and a user prompt.
    *   It runs the agent with the given prompt and returns the agent's response.
*   **`close_agent_sessions(cleanup_event: asyncio.Event, cleanup_task: asyncio.Task)`**:
    *   Triggers the `cleanup_event` and awaits the `cleanup_task` to ensure all MCP sessions are closed gracefully.

## 6. Prompts (`prompts.py`)

This file defines the `AGENT_SYSTEM_PROMPT`, which is crucial for guiding the AI agent's behavior and capabilities.

*   **`AGENT_SYSTEM_PROMPT`**:
    *   Instructs the agent to act as an AI assistant capable of searching Notion and Google Drive via n8n remote MCP.
    *   Defines the agent's identity as an "expert librarian" for internal digital assets, specialized in knowledge retrieval for project proposals.
    *   Outlines the agent's workflow: deconstruct request, formulate search queries, execute tool calls (`notion_search`, `gdrive_search`), analyze and rank results, and synthesize a clear, well-formatted summary.
    *   Specifies rules of engagement, including prioritizing actionable resources, handling "no results" gracefully, managing tool errors, and being concise.

## 7. Streamlit Application (`streamlit_app.py`)

This is the main entry point for the user interface.

*   **`run_async(coro, loop)`**:
    *   A helper function to execute asynchronous coroutines within Streamlit's synchronous environment using `nest_asyncio`.
*   **Page Configuration**:
    *   Sets the page title, icon, and layout for the Streamlit application.
*   **Header and Welcome Message**:
    *   Displays the application title and an introductory message.
*   **Initialization**:
    *   Checks if the agent is already in `st.session_state`. If not, it calls `initialize_session_state()` to set up the agent and its dependencies.
*   **Sidebar**:
    *   Displays the DataToBiz logo.
    *   **"Clear Chat History" button**: Resets the agent's conversation history and the displayed messages.
    *   **"End Session and Exit" button**: Triggers the `close_agent_sessions` function to gracefully shut down all MCP connections and stops the Streamlit application.
    *   **"About" section**: Provides a brief description of the chatbot's purpose and technology.
*   **Chat History Display**:
    *   Iterates through `st.session_state.messages` and displays each message in a chat bubble format.
*   **User Input and Response Logic**:
    *   `st.chat_input()`: Provides a text input field for the user to type their queries.
    *   When a user enters a prompt:
        *   The user's message is appended to `st.session_state.messages` and displayed.
        *   A "Thinking..." spinner is shown.
        *   `get_agent_response` is called asynchronously to get the agent's reply.
        *   The agent's response is displayed and appended to `st.session_state.messages`.
        *   Includes robust error handling for `ConnectionError` and other general exceptions, displaying detailed error messages to the user.

## 8. How to Run/Deploy

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mhussam-ai/mcp_chatbot.git
    cd mcp_chatbot
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    # Step 1: Create a Virtual Environment
    python -m venv .venv    
    # Or, using uv (a fast Python package manager): 
    uv venv .venv
    ```

    ```bash
    # Step 2: Activate the Virtual Environment
    .venv\Scripts\activate # On Windows
    source .venv/bin/activate # On macOS/Linux
    ```

    ```bash
    # Step 3: Install Dependencies
    pip install -r requirements.txt
    # Or, using uv (a fast Python package manager):
    uv pip install -r requirements.txt
    ```

3.  **Set up Google API Key:**
    *   Create a `.env` file in the root directory. 
    *   Add your Google API Key: `GOOGLE_API_KEY="your_google_api_key_here"`
    *   Alternatively, you can set it as an environment variable directly.

4.  **Ensure MCP Servers are accessible:**
    *   The `config.json` specifies `npx mcp-remote` commands. Ensure `npm` and `npx` are installed (part of Node.js).
    *   The remote MCP servers (Notion, n8n) must be active and accessible from your environment.
5.  **Run the Streamlit application:**
    ```bash
    streamlit run streamlit_app.py
    ```
    This will open the application in your web browser.

**Ensure `config.json` is present.**
**The local/deployment environment must have Node.js/npm installed** for the `npx mcp-remote` commands to work.

## 9. Key Concepts

*   **Model Context Protocol (MCP)**: A protocol that allows AI models to securely and dynamically access external tools and resources (like Notion databases or Google Drive files) through a standardized interface.
*   **Langchain**: A framework that simplifies the development of applications powered by large language models, providing tools for chaining LLM calls, managing memory, and integrating with external data sources.
*   **Streamlit**: An open-source Python library that makes it easy to create and share beautiful, custom web apps for machine learning and data science.
*   **Google Generative AI (Gemini-2.5-flash)**: A powerful large language model from Google capable of understanding and generating human-like text, used here to power the chatbot's reasoning and response generation.
*   **`nest_asyncio`**: A library that patches `asyncio` to allow its use in environments where an event loop is already running (e.g., some web frameworks or interactive notebooks), which is often the case with Streamlit.