# AgentSpaces repository — Usage guide (English)

Purpose
-------
This document explains how to set up, run, develop, and package "agents" inside the `agentspaces` repository. It is written in English and stored in the repository `documents/` folder.

Quick checklist
- [ ] Describe repository layout and important files
- [ ] Install dependencies and set up a Python environment
- [ ] Configure environment variables and project config
- [ ] Run the example agent (`DpxToClickhouse`)
- [ ] Debug and test the agent locally
- [ ] Create a new agent (step-by-step)
- [ ] Operational tips (LLM, MCP tools, outputs)

1. Overview
-----------
The `agentspaces` repository contains agent implementations organized as directed graphs (agentic graphs) that orchestrate multi-step workflows — for example: migrating DBT logic, extracting metadata, querying sheets, calling remote tools. Each agent lives under `agents/` and typically contains these files:

- `context.py` — initializes wrappers (LLM adapters, MCP client, configuration). This module is used by nodes to access shared resources.
- `node_functions.py` — defines the State (Pydantic model) and node functions. Each node accepts a State, updates it, and returns the updated State.
- `graph.py` — builds the `StateGraph`, registers nodes, implements the router and often contains a small debug runner.
- `prompts.md` — prompt templates used by LLM-driven nodes.
- `output_files/` — directory where agents write generated artifacts (SQL, YAML, etc.).

2. Prerequisites
----------------
- Python 3.10 or newer
- Git
- Recommended: use a virtual environment (venv)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # zsh
pip install -r requirements.txt
```

Note: `requirements.txt` lists packages used by the project (langchain, langchain-core, clickhouse clients, psycopg2, etc.). Adjust versions per your environment if needed.

3. Environment and configuration
--------------------------------
The repository may use `local.env` for environment variables. Agents typically load configuration via `variables.helper.ConfigLoader` and a module under `variables/agentspaces` (for example `variables.agentspaces.dpx2clickhouse`).

Important configuration keys used by `DpxToClickhouse` (refer to `node_functions.py` and `context.py` for exact names):

- `DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET` — Google Sheets spreadsheet id containing mapping from ClickHouse staging → DPX
- `DPX2CLICKHOUSE_PII_COLUMNS_SHEET` — Google Sheets spreadsheet id with PII columns per table
- `DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO` — GitLab project id or path for the ClickHouse DBT repo
- `DPX2CLICKHOUSE_DBT_TRINO_REPO` — GitLab project id or path for the DPX/Trino DBT repo

Example `local.env` (or export directly):

```bash
# local.env (example)
DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET="<your-mapping-sheet-id>"
DPX2CLICKHOUSE_PII_COLUMNS_SHEET="<your-pii-sheet-id>"
DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO="group/project-clickhouse"
DPX2CLICKHOUSE_DBT_TRINO_REPO="group/project-dpx"
```

Or export environment variables in your shell:

```bash
export DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET='<id>'
export DPX2CLICKHOUSE_PII_COLUMNS_SHEET='<id>'
export DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO='group/project-clickhouse'
export DPX2CLICKHOUSE_DBT_TRINO_REPO='group/project-dpx'
```

Important note: The agents attempt to bind `MCPClientWrapper` and LLM adapters (for example `GeminiLLM`) if the modules exist. If MCP or LLM wrappers are missing, the code will degrade gracefully but some nodes (Google Sheets lookups, GitLab fetches, LLM summarization) will not run.

4. Running the example agent: DpxToClickhouse
--------------------------------------------
The example agent lives in `agents/DpxToClickhouse`. There are two common ways to run it:

- Run the graph file directly (has a debug runner under `__main__`):

```bash
# from the repository root
python agents/DpxToClickhouse/graph.py
```

- Run programmatically from Python (useful for testing):

```python
# example: programmatically run the agent
from agents.DpxToClickhouse.graph import run_workflow
import asyncio
asyncio.run(run_workflow())
```

What happens when you run the agent:
- Configuration is loaded from `variables.agentspaces.dpx2clickhouse` via `ConfigLoader`.
- The agent will attempt to initialize LLM adapters if available.
- The state machine executes nodes in this order (router decides transitions):
  - `Orchestrator` → `ExtractStagingTable` → `QueryMapping` → `QueryPII` → `QueryGitlabDBTLogic` → `ExtractS3Path` → `FetchSchema` → `SummarizeMigration` → `WriteOutput`.

Output files are written to `agents/DpxToClickhouse/output_files/` by default, or to the directory pointed by `ctx.output_dir` if you set that in `context.py`.

5. Debugging & logging
----------------------
- The debug runner in `graph.py` prints each step and a final `last_state` so you can inspect messages and intermediate fields.
- Nodes append `SystemMessage` entries to `state.messages` which you can use to trace decisions and errors.
- If MCP or LLM are unavailable, nodes add messages like `No llm_gitlab_vetc available` to indicate the missing dependency. Inspect `context.py` to see which wrappers are present.

6. Creating a new agent (step-by-step)
-------------------------------------
Example: create a new agent `MyAgent`.

Checklist summary:
- [ ] Create `agents/MyAgent/` folder
- [ ] Add `context.py`, `graph.py`, `node_functions.py`, `prompts.md`, `output_files/`
- [ ] Define a `State` (Pydantic) in `node_functions.py`
- [ ] Implement node functions (each node accepts and returns State)
- [ ] Implement a `workflow_router` in `graph.py` that returns the next node name
- [ ] Add a `__main__` runner for quick debugging
- [ ] Add tests (unit/integration) as needed

Detailed steps

1) Copy the sample agent:

```bash
cp -R agents/DpxToClickhouse agents/MyAgent
```

2) Rename symbols and modules
- In `graph.py`: update imports to use your node functions, change `NODES`, `NODE_ORDER`, and `workflow_router` if necessary.
- In `node_functions.py`: rename `MigrationState` to `MyAgentState` (recommended) and adjust fields.
- Update `prompts.md` with templates for your agent.

3) Define the State contract
- Provide a clear list of input fields, intermediate fields, and outputs. Use type annotations and defaults.

4) Node design contract
- Node signature: f(state: State) -> State (or async equivalent)
- Validate required inputs and raise `ValueError` or append error messages to state for missing fields
- Keep side effects limited (prefer writing outputs in a dedicated node)
- Append `SystemMessage` or `HumanMessage` to `state.messages` for traceability

5) Router
- Implement `workflow_router(state: State) -> str` to return the next node name
- Ensure there is a path to the `END` state

6) LLM and tools
- If your agent uses LLMs, keep prompt templates in `prompts.md` and use `utils.common.prompt.prompt_loader` to render them
- If your agent uses remote tools, call them via `ctx.mcp.aexecute_tool(server, tool, payload)` and normalize results in helper functions

7) Runner & debug
- Add a debug runner similar to the sample `graph.py` that creates an initial_state and prints each step

7. Minimal skeleton example
---------------------------
Place this example in `agents/MyAgent/node_functions.py` as a starting point:

- State fields: `messages: List[BaseMessage]`, `input_text: Optional[str]`, `result: Optional[str]`
- Nodes: `orchestrator_node`, `process_node`, `write_output_node`

(Use the existing sample agent for precise patterns.)

8. Best practices & edge cases
------------------------------
- Always mock `ctx.mcp` and `ctx.llm_*` in unit tests to get deterministic behavior.
- Validate and sanitize any external inputs (sheets, git, db) before using them in transforms.
- Use UTC and explicit timezone handling when working with timestamps.
- Protect secrets and credentials; do not log them or include them in prompts to LLMs.
- The summarize step depends on the LLM returning well-formed JSON; implement checks and retries or fallback flows for invalid responses.

9. Next steps & extensions
--------------------------
- Add unit tests for all nodes (happy path + a few edge cases)
- Add CI pipeline to run linters, unit tests, and basic smoke tests
- Optionally expose an agent runner as a lightweight HTTP service for automation

10. Internal references
-----------------------
- The `agents/DpxToClickhouse/` folder is a full example you can use as a template
- Helpful modules: `utils/common/prompt`, `framework/mcp_adapters`, `variables/` config loaders

---

The specialized guide for `DpxToClickhouse` is located at `documents/agents/DpxToClickhouse.md`. If you want, I can also translate or expand the English versions of the other documents, add `local.env.example`, or scaffold unit tests.
