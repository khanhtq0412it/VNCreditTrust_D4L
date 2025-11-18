# MCP — Modular Control Protocol Servers

This repository contains a set of lightweight MCP (Modular Control Protocol) servers
that expose data-source specific tooling for ClickHouse, PostgreSQL, and Google Sheets.

Quick summary
-------------
- Entry points: `src/mcp_server/clickhouse_server.py`, `src/mcp_server/postgres_server.py`, `src/mcp_server/google_sheet_server.py`.
- Purpose: Wrap data-access logic (in `tools/`) and present it as small RPC tools via `FastMCP`.
- Deployment: Supports Docker Compose and Kubernetes (see `docs/deploy.md`).

Where to start
--------------
- Read `docs/architecture.md` for repository architecture.
- Read `docs/usage.md` for usage and local run instructions.
- Copy `.env.example` to `.env` and fill in secrets before running.

Project layout
--------------
- `src/mcp_server/` — MCP server entrypoints.
- `tools/` — Data access and helper logic used by MCPs.
- `variables/` — Env/config helpers.
- `config/` — Static configuration files.
- `k8s/` — Kubernetes manifests for deploying MCPs.
- `docs/` — Additional documentation (architecture, usage, deploy).

Contact
-------
For questions about this repo or the MCP design, reach out to the team that maintains the data platform.
