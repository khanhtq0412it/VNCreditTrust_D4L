# MCP REPOSITORY — USAGE GUIDE

This document explains how to run and use the MCP servers in this repository. When the doc refers to files or paths, filenames are CAPITALIZED (for example: `README.MD`, `.ENV.EXAMPLE`, `SRC/MCP_SERVER/CLICKHOUSE_SERVER.PY`).

CHECKLIST
- [x] Describe prerequisites and environment configuration
- [x] Instructions to install dependencies locally
- [x] How to run each MCP server locally
- [x] Minimal examples of how to call the exposed tools (examples/pseudocode)
- [x] Troubleshooting and next steps

1) PREREQUISITES

- Python 3.10+ installed.
- `pip` available and network access to install dependencies from `requirements.txt`.
- Network access to upstream data services (ClickHouse, Postgres) for real usage, or local mock endpoints for testing.
- A copy of `.ENV.EXAMPLE` configured as `.ENV` with the required credentials before starting servers.

2) CONFIGURATION (ENVIRONMENT VARIABLES)

1. Copy the example env file:

```bash
cp .ENV.EXAMPLE .ENV
```

2. Edit `.ENV` and fill in service credentials and hostnames. Key groups in `.ENV`:
- ClickHouse variables: `CLICKHOUSE__HOST`, `CLICKHOUSE__PORT`, `CLICKHOUSE__USER`, `CLICKHOUSE__PASSWORD`
- Postgres variables: `POSTGRES__HOST`, `POSTGRES__PORT`, `POSTGRES__USER`, `POSTGRES__PASSWORD`, `POSTGRES__DB_NAME`
- Google Sheets service account: `GOOGLE_SHEETS__SERVICE_ACCOUNT_JSON_PATH` or `GOOGLE_SHEETS__SERVICE_ACCOUNT_JSON`
- GitLab integration flags and tokens (optional): `GITLAB__PERSONAL_ACCESS_TOKEN`, `GITLAB__API_URL`, etc.

3) INSTALL DEPENDENCIES

Create a Python virtual environment and install dependencies from `REQUIREMENTS.TXT`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4) RUNNING MCP SERVERS LOCALLY

Each MCP server is a standalone Python process. Recommended pattern: run each server in its own terminal or use process manager / container.

- ClickHouse MCP

```bash
# Run the ClickHouse MCP server
python SRC/MCP_SERVER/CLICKHOUSE_SERVER.PY
```

Default listening port: 8080.

- Postgres MCP

```bash
python SRC/MCP_SERVER/POSTGRES_SERVER.PY
```

Default listening port: 8081.

- Google Sheets MCP

```bash
python SRC/MCP_SERVER/GOOGLE_SHEET_SERVER.PY
```

Default listening port: 8082.

The servers log to stdout; use the logs to confirm readiness and debug errors. Each server configures logging via `logging.basicConfig(level=logging.INFO)`.

5) EXAMPLES: CALLING MCP TOOLS (PSEUDO CLIENTS)

MCP servers register named tools via the `FastMCP` framework (using `@mcp.tool()`). Clients must use the same transport the server was started with (the default used here is `streamable-http`). The exact wire format depends on `FastMCP`'s transport implementation. Below are example patterns and payloads (pseudo-requests). If you have an SDK or client library for `FastMCP` in your environment, prefer that.

A. ClickHouse: `clickhouse_query`
- Tool name: `clickhouse_query`
- Argument: `sql_query` (string)

Example (pseudo-JSON payload):

```json
{
  "tool": "clickhouse_query",
  "args": { "sql_query": "SELECT count(*) FROM datamart.user_sessions" }
}
```

Expected response: JSON array of records (or an error message object).

B. ClickHouse: `clickhouse_table_schema`
- Tool name: `clickhouse_table_schema`
- Argument: `table_name` (string, fully qualified, e.g. `datamart.user_sessions`)

C. Postgres: `postgres_query`
- Tool name: `postgres_query`
- Argument: `sql_query` (string)

D. Postgres: `postgres_airflow_dag_status`
- Tool name: `postgres_airflow_dag_status`
- Argument: `dag_id` (string)

E. Google Sheets: `google_sheet_query`, `google_sheet_tabs`, `google_sheet_title`
- `google_sheet_query` args: `spreadsheet_id`, optional `range_name`, `use_json_path`, `header`
- `google_sheet_tabs` args: `spreadsheet_id`, optional `use_json_path`
- `google_sheet_title` args: `spreadsheet_id`, optional `use_json_path`

Notes on client usage:
- If you don't have a `FastMCP` client, use the HTTP transport wrapper or write a small client using the same `streamable-http` conventions — check your project's `mcp` package documentation or contact the platform team for a client example.
- All handlers return JSON-serializable responses. DataFrames are serialized with `orient='records'` and ISO date formatting.

6) RUNNING WITH DOCKER OR DOCKER-COMPOSE

The repository includes a `DOCKERFILE` and `DOCKER-COMPOSE.YAML` in the root. A quick local container run:

```bash
# Build the image (example tag)
docker build -t vetc/mcp:local .

# Run with compose (reads .env automatically)
docker compose up --build
```

Adjust the image name and compose service names as needed. See `DOCS/DEPLOY.MD` for more detailed deployment instructions.

7) RUNNING IN KUBERNETES

See `DOCS/DEPLOY.MD` for the full Kubernetes deployment process. In brief:

1. Build and push the container image to your registry.
2. Create a namespace and a secret from `.ENV`.
3. Apply the `K8S/` manifests in this repo:

```bash
kubectl create ns mcp
kubectl -n mcp create secret generic mcp-env --from-env-file=.env
kubectl -n mcp apply -f k8s/
```

8) TROUBLESHOOTING

- Server not starting:
  - Confirm `.ENV` exists and contains required variables.
  - Check logs for stack traces.
  - Confirm the Python environment has `requirements.txt` installed.

- Tool returns error JSON:
  - The handlers wrap exceptions and return an object like `{ "status": "ERROR", "message": "..." }`.
  - Consult logs for the full stack trace.

- Connectivity issues to ClickHouse/Postgres:
  - Verify network access (firewalls, CLUSTER IPs, or VPN) and connection parameters in `.ENV`.

9) EXTENDING THE PROJECT

To add a new MCP service:
1. Implement helper functions in `TOOLS/<NEW>/` (follow existing packages' patterns).
2. Create `SRC/MCP_SERVER/<NEW>_SERVER.PY` that:
   - Creates a `FastMCP` instance.
   - Registers `@mcp.tool()` wrappers that call helpers and return JSON.
3. Add any new environment variables to `.ENV.EXAMPLE` and `.ENV`.
4. Add container/Dockerfile/K8s manifests as needed.

10) CONTACT AND OWNER

Refer to `README.MD` for the repo summary and owners. If unsure about `FASTMCP` transport details or expected client libraries, contact your internal platform team who maintains `MCP` and `FastMCP` packages.
