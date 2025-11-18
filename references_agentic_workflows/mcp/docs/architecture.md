# MCP Repository — Architecture

This document describes the high-level architecture of the MCP (Modular Control Protocol) repository.

Overview
--------
The repository hosts lightweight MCP servers that expose data sources (ClickHouse, PostgreSQL, Google Sheets)
as remote-callable tools. Each MCP server wraps domain-specific logic implemented in the `tools/` and `variables/` modules
and exposes a small set of JSON-over-HTTP (streamable-http) endpoints via the `FastMCP` framework.

Top-level layout
----------------
- `src/mcp_server/` - Entrypoints for each MCP server process:
  - `clickhouse_server.py` — ClickHouse tools (port 8080 by default).
  - `postgres_server.py` — Postgres tools (port 8081 by default).
  - `google_sheet_server.py` — Google Sheets tools (port 8082 by default).

- `tools/` - Implements the data access and business logic used by server entrypoints. Example subpackages:
  - `tools/clickhouse/` — ClickHouse query helpers.
  - `tools/postgres/` — Postgres query helpers.
  - `tools/google_sheet/` — Google Sheets helpers.

- `variables/` - Environment/config loader helpers used by the tool modules.

- `config/` - Static configuration JSONs (for example `mcp.json`).

- `docs/` - Documentation (this and other docs).

Runtime architecture
--------------------
Each MCP server starts a `FastMCP` instance and registers tools using the `@mcp.tool()` decorator. The MCP server exposes an
RPC-like HTTP transport (streamable-http). Clients can call the named tools with JSON-serializable arguments and will receive
JSON responses.

Example call flow (ClickHouse query):
1. Client sends a `clickhouse_query` call with `sql_query` argument to the ClickHouse MCP.
2. The MCP handler (`clickhouse_query`) logs the request and calls `tools.clickhouse.clickhouse_tools.query_clickhouse_logic`.
3. The helper connects to ClickHouse, runs the query, converts the result to a pandas DataFrame, and returns it.
4. The MCP handler converts the DataFrame to JSON and returns it to the client.

Security and configuration
--------------------------
- Secrets and connection settings are provided through environment variables (see `.env.example`).
- The MCP servers are intentionally lightweight; place them behind internal network ACLs or secure ingress when exposing to broader networks.

Extensibility
-------------
To add a new data source, create a new `src/mcp_server/<data_source>_server.py` that:
- Instantiates a `FastMCP` on an unused port.
- Imports helper functions from `tools/<data_source>`.
- Registers `@mcp.tool()` functions that return JSON-compatible responses.

Operational notes
-----------------
- Each server can run as a standalone process or be containerized.
- For deployment, the repo supports Docker Compose and Kubernetes manifests (see `docs/deploy.md`).

