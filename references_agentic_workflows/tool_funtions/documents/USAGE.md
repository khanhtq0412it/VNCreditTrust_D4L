# Usage Guide

This document explains how to use the public tool functions in this repository. It contains examples, return conventions, configuration hints, and troubleshooting tips.

## Quick start

1. Create and activate a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

2. Set the required environment variables for the connector(s) you need (see "Configuration and credentials" below). For local development you can place them in `local.env` and load them with your shell.

3. Import and call the tool functions from `tools/`.

## Example: Google Sheets

```python
from tools.google_sheet.google_sheet_tools import query_google_sheet_data, query_google_sheet_tabs

spreadsheet_id = "YOUR_SPREADSHEET_ID"
# Read a specific range (A1 notation). header=True uses the first row as column names.
df = query_google_sheet_data(spreadsheet_id, range_name="Sheet1!A1:D100", header=True)
print(df.head())

# List tabs
tabs = query_google_sheet_tabs(spreadsheet_id)
print(tabs)
```

## Example: ClickHouse

```python
from tools.clickhouse.clickhouse_tools import query_clickhouse_logic

sql = "SELECT count(*) AS cnt FROM events_dbt"
df = query_clickhouse_logic(sql)
print(df)
```

## Example: PostgreSQL

```python
from tools.postgres.postgres_tools import query_postgres_logic, query_postgres_airflow_dag_status

# Arbitrary SQL
df = query_postgres_logic("SELECT now() as ts")
print(df)

# Latest Airflow DAG run status
status = query_postgres_airflow_dag_status("dag_notification_event")
print(status)  # dict or None
```

## Return types and conventions

- Tabular results: `pandas.DataFrame`.
- Single-record metadata: Python `dict` or simple `str`.
- Empty result sets: `DataFrame.empty == True` or `None` for single-record lookups.
- Errors: Tool functions raise `RuntimeError` with contextual messages; check logs for underlying exception details.

## Configuration and credentials

Configuration is centralized in `variables/` and loaded via the project's config helper. The most commonly used environment variables are:

- Google Sheets
  - `GOOGLE_SHEET_SERVICE_ACCOUNT` (JSON string containing the service account) OR
  - `GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH` (filesystem path to the service account JSON)

- ClickHouse
  - `CLICKHOUSE_HOST`
  - `CLICKHOUSE_PORT`
  - `CLICKHOUSE_USER`
  - `CLICKHOUSE_PASSWORD`

- Postgres
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_USER`
  - `POSTGRES_PASS`
  - `POSTGRES_DB_NAME`

Place development variables in `local.env` (do not commit secrets). Example `local.env` entry:

```text
# Google Sheets
GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH=/path/to/service-account.json

# ClickHouse
CLICKHOUSE_HOST=clickhouse.local
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=svc_user
CLICKHOUSE_PASSWORD=secret

# Postgres
POSTGRES_HOST=postgres.local
POSTGRES_PORT=5432
POSTGRES_USER=svc_user
POSTGRES_PASS=secret
POSTGRES_DB_NAME=my_db
```

Load them in macOS/zsh for a session:

```bash
export $(grep -v '^#' local.env | xargs)
```

## Logging and debugging

- Modules use standard Python `logging`. To enable debug logs, set `LOG_LEVEL=DEBUG` in your environment.
- Inspect provider-level modules in `utils/connector/<backend>/providers.py` for low-level errors and request/response handling.

## Best practices

- Call tool functions from short-lived processes (scripts, jobs) or wrap them behind a small HTTP/API layer if you need a long-running service.
- Avoid embedding secrets in code; use environment variables or a secret manager.
- Mock provider functions in unit tests to avoid hitting external systems.

## Troubleshooting

- Google authentication errors: confirm the service account JSON (string vs file path) and that the service account has access to the target spreadsheet.
- Database connection errors: verify host/port/credentials and network connectivity (firewall, VPC rules).
- Unexpected empty DataFrame: double-check SQL/range parameters and that the source contains data.

## Further reading

- See `tools/` for public entry points.
- See `utils/connector/` for connector implementations and authentication details.

