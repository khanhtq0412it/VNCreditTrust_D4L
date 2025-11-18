# LangGraph Server (framework/langgraph_server)

Purpose
-------
Provide a lightweight HTTP server to run and inspect agent graphs under the `agents/` folder. The server streams the graph execution (via `app.astream(initial_state)`) and returns a step-by-step snapshot of node states and messages.

Install prerequisites
---------------------
This module expects `FastAPI` and `uvicorn` for the server. Install with pip:

```bash
pip install fastapi uvicorn pydantic
```

Run the server
--------------
From the repository root run:

```bash
uvicorn framework.langgraph_server.server:app --host 0.0.0.0 --port 8000
```

Endpoints
---------
- `GET /agents` — list agent folder names that contain a `graph.py` file.
- `POST /run/{agent_name}` — run the chosen agent. Body: `{"initial_state": {...}}` (optional)
  - Response: `{agent: <name>, steps: [ ... ] }` where `steps` is an array of node-state snapshots.

How this helps observe Langsmith traces
--------------------------------------
Langsmith is LangChain's experiment/tracing UI. The server returns the state messages and node messages, including LLM SystemMessage/HumanMessage content. To see rich Langsmith traces for LLM calls (tools, chains), configure LangChain to enable Langsmith tracing in standalone mode by setting up the `LANGCHAIN_TRACING_V2` environment variables and Langsmith API key.

Example environment variables for Langsmith standalone tracing (local):

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.langchain.com"  # or local Langsmith endpoint if self-hosted
export LANGCHAIN_API_KEY="<your-langsmith-api-key>"
```

Notes & limitations
-------------------
- The server dynamically imports the agent's `graph.py` module. Module import may execute top-level code in the agent (e.g., `asyncio.run(discover_tools())` in `context.py`). Ensure your environment variables and dependencies are set before calling `/run`.
- The server attempts to normalize non-serializable objects by converting them to strings.
- The server is intentionally simple and designed for developer inspection. For production, secure the server and handle authentication, rate limiting and secrets management.

Security
--------
- Do not run this server in production without proper authentication.
- Avoid exposing credentials via environment variables on untrusted machines.

Troubleshooting
---------------
- If an agent fails to import, inspect printed exceptions in the server logs for missing imports or missing dependencies.
- Many agents expect an MCP client and LLM adapters to be available; without them, some nodes will add messages but the workflow may not complete.


