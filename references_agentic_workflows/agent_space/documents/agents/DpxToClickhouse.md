# DpxToClickhouse Agent — Usage Guide

This document explains how the `DpxToClickhouse` agent works, how to run it, debug it, and extend it. The agent code lives in `agents/DpxToClickhouse`.

Contents
- Purpose
- Directory layout
- Workflow (high-level)
- Important files and responsibilities
- Installation and run steps
- Example inputs and expected outputs
- How to create a new agent based on this one
- Debugging, testing, and operational notes

1. Purpose
----------
The `DpxToClickhouse` agent helps migrate ClickHouse DBT staging models to source directly from DPX. The agent:
- Extracts a staging table name from user input
- Looks up mapping records (ClickHouse staging → DPX metadata) in Google Sheets
- Reads PII column lists from a sheet
- Retrieves DBT model logic from GitLab for staging, raw, and DPX models
- Fetches the current staging schema
- Uses an LLM to generate a rewritten staging SQL model and corresponding schema YAML according to strict requirements
- Writes generated `.sql` and `_schema.yaml` files to `output_files/`

2. Directory layout (key files)
-------------------------------
- `context.py` — configuration, LLM initialization, MCP client and tool discovery
- `graph.py` — builds the StateGraph, the router and a debug runner
- `node_functions.py` — defines `MigrationState` (Pydantic) and all nodes used by the workflow
- `prompts.md` — prompt templates used by LLM calls
- `output_files/` — output directory where generated files are saved

3. Workflow (high level)
-------------------------
Nodes executed in sequence (router decides next node based on state):
1. Orchestrator — set up `mapping_sheet_id` and `pii_sheet_id` and publish a SystemMessage prompt
2. ExtractStagingTable — extract staging table name from human input (LLM or fallback)
3. QueryMapping — retrieve mapping row from Google Sheet
4. QueryPII — read PII column list from Google Sheet
5. QueryGitlabDBTLogic — fetch DBT logic for staging/raw/DPX from GitLab
6. ExtractS3Path — get DPX MinIO path using a Postgres query
7. FetchSchema — fetch the current staging table schema
8. SummarizeMigration — use LLM to generate the new staging DBT model and YAML (LLM must return strict JSON)
9. WriteOutput — write generated SQL and YAML to disk

Router logic is implemented in `workflow_router` inside `graph.py`.

4. Important files explained
---------------------------
- `context.py`:
  - Adds repo root to `sys.path` for absolute imports.
  - Loads `dpx2clickhouse_config` via `ConfigLoader.load_single(Dpx2Clickhouse)`.
  - Attempts to import `GeminiLLM` (from `utils.llm.gemini.module`) and `MCPClientWrapper` (from `framework.mcp_adapters.server`). If unavailable, falls back to None.
  - Discovers MCP tools (`google_sheet_query`, GitLab related tools) asynchronously at import time.

- `node_functions.py`:
  - `MigrationState`: Pydantic model storing messages and all intermediate/final state fields.
  - `orchestrator_node()`: sets sheet ids and appends a `SystemMessage` containing the instruction prompt.
  - `extract_stg_table_node()`: extracts the ClickHouse staging table name from the human messages using an LLM (fallback: last token).
  - `query_google_sheet()`: helper that calls MCP tool `google_sheet_query` if `ctx.mcp` is available.
  - `fetch_clickhouse_schema()` and `fetch_dbt_logic()`: use helper utilities to fetch DBT model schema and SQL logic.
  - `summarize_migration_node()`: renders the prompt from `prompts.md` and calls `ctx.llm_summary.invoke()`; expects a JSON string containing `generated_stg_dbt_model` and `generated_stg_schema_yaml`.
  - `write_output_node()`: writes the SQL and YAML files into `output_files/` or into the path defined by `ctx.output_dir`.

- `prompts.md`: contains the LLM templates. The main summarize prompt requires a strict JSON output of two fields only.

5. Installation & run steps
--------------------------
1) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # zsh
pip install -r requirements.txt
```

2) Provide configuration environment variables (see section below) using `local.env` or `export`.

3) Run the agent (quick run):

```bash
python agents/DpxToClickhouse/graph.py
```

4) Or run programmatically (useful for tests):

```python
from agents.DpxToClickhouse.graph import run_workflow
import asyncio
asyncio.run(run_workflow())
```

Output files will be created in `agents/DpxToClickhouse/output_files/` unless `ctx.output_dir` is set.

6. Required configuration (key env variables / config keys)
----------------------------------------------------------
The agent expects a config object loaded by `variables.helper.ConfigLoader`. The following keys are used in the code and must be present in that config:
- `DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET` — Google Sheets spreadsheet id for mapping staging → DPX
- `DPX2CLICKHOUSE_PII_COLUMNS_SHEET` — Google Sheets spreadsheet id for PII columns per table
- `DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO` — GitLab project id or path for the ClickHouse DBT repository
- `DPX2CLICKHOUSE_DBT_TRINO_REPO` — GitLab project id or path for the DPX/Trino DBT repository

Credentials for MCP (if used), GitLab and Google APIs must be mounted/provided via your MCP adapter or environment in a secure way. If MCP or LLM wrappers are missing, the agent has partial fallbacks, but the workflow will not be complete.

7. Example input and expected outcome
-------------------------------------
Input (HumanMessage example):

"Get information about ClickHouse staging and DPX tables, including PII columns and dbt logic. Table: staging_prod_db_coredb_crm_owner_account"

Expected behavior:
- Agent will extract `staging_prod_db_coredb_crm_owner_account`.
- It will find mapping row in the mapping sheet and set DPX metadata (catalog, schema, table_id...).
- It will obtain PII columns, DBT logic and schema, call LLM to generate the new `dpx_`-prefixed SQL and YAML, then write them to `output_files/`.

8. How to create a new agent (step-by-step)
-------------------------------------------
To create a new agent `MyAgent` based on this pattern:
1. Copy `agents/DpxToClickhouse` to `agents/MyAgent`.
2. Edit `node_functions.py`: rename the `State` model (e.g., `MyAgentState`) and adjust fields to the inputs and outputs your agent needs.
3. Edit `prompts.md` to contain prompt templates relevant to your domain.
4. Edit `graph.py` to import the right node functions, create `NODES` and `NODE_ORDER`, and implement a `workflow_router(state)` that returns the next node name.
5. Ensure each node is a pure function: accepts and returns the `State` object and appends `SystemMessage`/`HumanMessage` where suitable for tracing.
6. Add a debug runner (`if __name__ == '__main__'`) using an example initial state and `app.astream` loop like the sample.
7. Add unit tests that mock `ctx.mcp` and `ctx.llm_*` to assert node behavior deterministically.

9. Debugging and testing tips
----------------------------
- If networked tools (MCP, GitLab) are missing, mock `ctx.mcp` to return deterministic values.
- Inspect `state.messages` to trace decisions made by the workflow.
- Use the debug runner in `graph.py` which prints each step and final `last_state`.
- For the summarize step, ensure your LLM or tool returns valid JSON with the two required fields; otherwise the node will log a JSON decode error in `state.messages`.

10. Security and production notes
--------------------------------
- Never commit credentials or tokens to source control.
- Limit LLM temperatures and check token usage for large prompts.
- Validate generated SQL/YAML manually before deploying into DBT production.

---

This document is intended as a developer reference for using and extending the `DpxToClickhouse` agent. If you want, I can add a sample `local.env.example` and a couple of unit test templates that mock `ctx` objects.
