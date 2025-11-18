"""
MCP Server for PostgreSQL Integration

This module exposes PostgreSQL-related data operations via an MCP (Modular Control Protocol)
server interface. It allows remote clients (e.g., AI agents, orchestration services)
to query Postgres for analytics, Airflow DAG monitoring, and Superset metadata lookups.

Functions exposed:
- query_postgres_logic
- query_postgres_airflow_dag_status
- query_postgres_superset_clickhouse_dashboards
"""

import json
import logging
from mcp.server.fastmcp import FastMCP
from tools.postgres.postgres_tools import (
    query_postgres_logic,
    query_postgres_airflow_dag_status,
    query_postgres_superset_clickhouse_dashboards,
)

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize MCP server
mcp = FastMCP("Postgres MCP Server", host="0.0.0.0", port=8081)

# -------------------------------
# MCP Tools Registration
# -------------------------------

@mcp.tool()
async def postgres_query(sql_query: str) -> str:
    """
    Executes an arbitrary SQL query on the PostgreSQL database.

    Args:
        sql_query (str): The SQL query string to execute.

    Returns:
        str: Query results as a JSON string.
    """
    try:
        logger.info("Executing Postgres query via MCP...")
        df = query_postgres_logic(sql_query)
        return df.to_json(orient="records", date_format="iso")
    except Exception as err:
        logger.error(f"Postgres query failed: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def postgres_airflow_dag_status(dag_id: str) -> str:
    """
    Retrieves the most recent execution status of an Airflow DAG from Postgres metadata.

    Args:
        dag_id (str): The Airflow DAG ID to check.

    Returns:
        str: Latest DAG run info as JSON string, or 'None' if not found.
    """
    try:
        logger.info(f"Querying Airflow DAG status for: {dag_id}")
        result = query_postgres_airflow_dag_status(dag_id)
        return json.dumps(result or {"message": "No DAG run found."}, default=str)
    except Exception as err:
        logger.error(f"Error fetching DAG status for {dag_id}: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def postgres_superset_dashboards(table_list: str) -> str:
    """
    Retrieves Superset dashboards and charts related to one or more ClickHouse tables.

    Args:
        table_list (str): Comma-separated table names.

    Returns:
        str: Dashboard and chart mappings as JSON string.
    """
    try:
        logger.info(f"Querying Superset dashboards for tables: {table_list}")
        result = query_postgres_superset_clickhouse_dashboards(table_list)
        return json.dumps(result, default=str)
    except Exception as err:
        logger.error(f"Error fetching Superset dashboards: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})

if __name__ == "__main__":
    mcp.run(transport="streamable-http")