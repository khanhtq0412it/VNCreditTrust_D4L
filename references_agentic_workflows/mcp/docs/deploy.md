# MCP Repository — Deployment Guide

This document explains how to deploy the MCP servers using Docker Compose and Kubernetes.

Environment variables
---------------------
Create a `.env` file from `env.example` and provide all required connection strings and secrets.

Docker Compose (quick local deploy)
-----------------------------------
A `docker-compose.yaml` exists at the repo root. To run the services locally:

1. Build or pull the image(s) used by the compose file.
2. Start the stack:

```bash
docker compose up -d --build
```

3. Check logs per service:

```bash
docker compose logs -f <service_name>
```

Kubernetes (production-ready)
-----------------------------
This repo includes Kubernetes manifests under `k8s/` that deploy each MCP server as a Deployment and a Service. The provided manifests are minimal and intended for internal clusters (e.g., EKS/GKE/AKS or on-prem).

High-level approach:
1. Create a namespace (optional):

```bash
kubectl create ns mcp
```

2. Create a secret for environment variables (sensitive values only):

```bash
kubectl -n mcp create secret generic mcp-env --from-env-file=.env
```

3. Apply the manifests:

```bash
kubectl apply -n mcp -f k8s/
```

4. Verify pods and services:

```bash
kubectl -n mcp get pods,svc
kubectl -n mcp logs deploy/clickhouse-mcp -c clickhouse-mcp
```

Ingress and security
--------------------
- Use an internal LoadBalancer or cluster-local Service for internal-only access.
- For external exposure, create an ingress (NGINX/ALB) with TLS, IP-based allowlists, or mTLS.
- Limit RBAC for service accounts and use NetworkPolicies to restrict access to upstream databases.

Scaling and resource tuning
---------------------------
- Set requests/limits in the Deployment specs based on observed CPU/memory usage.
- Consider HPA rules if the traffic pattern is variable. MCP servers are synchronous wrappers and may be I/O bound (DB/API calls).

Observability
-------------
- Ship container logs to your central logging (ELK, Loki, CloudWatch).
- Add readiness and liveness probes for each MCP container.
- Add Prometheus metrics exporter if you need quantitative observability.

# MCP Repository — Usage Guide

This guide explains how to run, use, and extend the MCP servers in this repository.

Prerequisites
-------------
- Python 3.10+ (project requirements are listed in `requirements.txt`).
- Network access to the target data stores (ClickHouse, Postgres, Google APIs) or local mock equivalents.
- A `.env` file with the required environment variables (copy `env.example` to `.env` and fill in secrets).

Install dependencies
--------------------
Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configuration
-------------
Copy `env.example` to `.env` and fill in connection strings and credentials. The MCP servers read configuration from environment variables at startup.

Running locally (standalone)
----------------------------
Each server is runnable as a standalone Python process.

- ClickHouse MCP

```bash
python src/mcp_server/clickhouse_server.py
```

- Postgres MCP

```bash
python src/mcp_server/postgres_server.py
```

- Google Sheets MCP

```bash
python src/mcp_server/google_sheet_server.py
```

By default, the servers bind to 0.0.0.0 and ports 8080, 8081, and 8082 respectively.

Using the MCP endpoints
-----------------------
These servers expose tools registered via the `FastMCP` framework. They are consumable by clients that speak the streamable-http transport or via HTTP wrappers. Example usage pattern:

- Send a JSON-encoded RPC call with the tools name and arguments.
- Receive a JSON response with the requested data.

Examples (pseudo-client):

- ClickHouse query:
  - Tool: `clickhouse_query`
  - Args: `{ "sql_query": "SELECT count(*) FROM datamart.user_sessions" }`

- Google Sheets:
  - Tool: `google_sheet_tabs`
  - Args: `{ "spreadsheet_id": "<ID>", "use_json_path": false }`

Adding a new MCP server
-----------------------
1. Add helpers to `tools/<new_source>/` implementing the core logic.
2. Add a new server file `src/mcp_server/<new_source>_server.py` mirroring existing servers.
3. Choose a listening port and add any necessary env vars to `.env.example`.
4. Test locally and add Docker/K8s manifests in `k8s/`.

Debugging and logs
------------------
- Each server configures basic logging via `logging.basicConfig(level=logging.INFO)`; check server stdout/stderr for logs.
- Exceptions are caught in the tool handlers and returned as JSON errors. Use the logs to diagnose stack traces.


