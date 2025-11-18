# Fundamentals: Agentic Graphs, State, MCP & Tools

This document explains core concepts the repository uses: agent, agentic graph, nodes, state, MCP (Multi-Cloud Platform adapters in this repo), and tools. It is written as a developer primer to help you design new agents and reason about existing ones.

Contents
- What is an Agent?
- Agentic Graphs and StateGraph
- Nodes (functions) and the router
- State object (Pydantic contract)
- Tools and MCP adapters
- LLM bindings
- Design patterns and best practices
- Testing strategies

1. What is an Agent?
---------------------
An agent in this repository is a small autonomous workflow that performs a multi-step task through a sequence of pure functions (nodes) operating on a shared State object. It often orchestrates calls to external services (LLM, Google Sheets, GitLab, databases) and produces artifact(s) as outputs.

Key properties:
- Deterministic node contracts: each node accepts a State and returns a modified State.
- Centralized orchestration logic via a router that inspects the State and decides the next node.
- Clear separation of concerns: nodes do one logical step (query, parse, transform, write).

2. Agentic Graphs & `StateGraph`
---------------------------------
Agentic graphs are directed graphs where vertices represent nodes (functions) and edges represent allowed transitions. `StateGraph` is the pattern used in the codebase (imported from `langgraph.graph`) to build and compile a stateful workflow.

- Nodes are registered with names and functions.
- A special `START` node is used to jump into the first real node.
- Router functions can be added as conditional edges to decide next node based on the `State`.
- `app.astream(initial_state)` (async iterator) drives the state transitions and yields intermediate step contexts for inspection.

3. Nodes (functions) and router
-------------------------------
- Node signature: f(state: State) -> State (or async variant when needed)
- Nodes may append messages to `state.messages` for traceability.
- Nodes should validate preconditions and raise `ValueError` or append an error message if input is missing.
- Router function: f(state: State) -> str (node name) which returns the next node to execute.

4. State object (Pydantic contract)
-----------------------------------
Use a Pydantic `BaseModel` for the State to gain validation, defaults, and clear structure. Example fields:
- `messages: List[BaseMessage]` — message queue for human/system/LLM messages
- input identifiers (e.g., `mapping_sheet_id`, `pii_sheet_id`)
- intermediate fields (e.g., `clickhouse_stg_table`, `dpx_table_id`)
- fetched artifacts (e.g., `stg_table_schema`, `stg_sql_logic`)
- outputs (e.g., `generated_stg_dbt_model`, `generated_stg_schema_yaml`)

Contract rules:
- Use type annotations
- Keep state mutation limited and predictable
- Prefer adding `SystemMessage` entries instead of raising exceptions for non-fatal issues

5. Tools & MCP adapters
-----------------------
MCP (here represented by `framework.mcp_adapters.server.MCPClientWrapper`) is a thin adapter that exposes remote tools (Google Sheets query, Postgres query, GitLab read) as RPC-like calls.

Tool pattern:
- Discover tools via `mcp.aget_tools(server_name, tool_name)`
- Execute a tool via `mcp.aexecute_tool(server_name, tool_name, payload)` (async) or `mcp.execute_tool(...)` (sync) depending on wrapper

Design tips:
- Treat tools as side-effectful primitives. Wrap them in small helper functions to isolate error handling and result normalization.
- Mock MCP in tests to simulate remote responses.

6. LLM bindings
----------------
LLMs are wrapped in adapter classes (e.g., `GeminiLLM`) exposing a simple interface:
- `get_llm()` returns a model instance
- `invoke(prompt)` returns an object with `.content`
- `bind_tools(tools)` attaches tool metadata if the LLM supports tool calls

Use `prompts.md` to store prompt templates and a small `prompt_loader` util to render them. Keep prompts small but complete and prefer structured outputs (JSON) for machine parsing.

7. Design patterns & best practices
-----------------------------------
- Single responsibility: nodes do one thing well.
- Immutability-ish: operate on a single State object, minimize external side effects, and centralize writes to `output_files/`.
- Clear error handling: append messages to `state.messages` and let the router decide to retry or abort.
- Prompt engineering: where LLM decisions are required, define precise templates and strict output contracts.
- Security: never log credentials and avoid sending secrets to LLMs.

8. Testing strategies
---------------------
- Unit test nodes by creating a minimal `State` and asserting returned state changes.
- Mock `ctx.mcp` and `ctx.llm_*` to return deterministic values.
- Integration tests: spin up a local MCP-like stub that listens for RPC calls (or use recorded fixtures).
- Test failure modes: missing mapping row, invalid JSON returned from LLM, missing PII sheet.

---

This fundamentals doc is intended to be a compact reference for developers creating or reviewing agents in this repository. If you want, I can add diagrams (ASCII or mermaid) or example unit tests for each node pattern.
