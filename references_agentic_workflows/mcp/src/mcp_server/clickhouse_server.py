"""
ClickHouse MCP Server
=====================

This module defines a production-grade MCP (Modular Control Protocol) server
for ClickHouse. It exposes key ClickHouse querying and metadata retrieval
capabilities to external agents or orchestration services.

Available Tools:
    1. `clickhouse_query` — Execute read-only SQL queries.
    2. `clickhouse_table_schema` — Retrieve schema metadata for a given table.
    3. `clickhouse_airflow_metadata` — Map Airflow DAGs to dbt data models.

Usage:
    $ python mcp_clickhouse_server.py
"""

import asyncio
import json
import logging
from mcp.server.fastmcp import FastMCP
from tools.clickhouse.clickhouse_tools import (
    query_clickhouse_logic,
    query_clickhouse_schema_logic,
    query_airflow_dags_by_dbt_table,
    query_dbt_tables_by_airflow_dag
)

# ---------------------------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# MCP Server Initialization
# ---------------------------------------------------------------------------
mcp = FastMCP("ClickHouse MCP Server", host="0.0.0.0", port=8080)

# ---------------------------------------------------------------------------
# MCP Tools Registration
# ---------------------------------------------------------------------------


@mcp.tool()
async def clickhouse_query(sql_query: str) -> str:
    """
    Executes a read-only SQL query on ClickHouse.

    Args:
        sql_query (str): The SQL query string to execute.

    Returns:
        str: JSON string of query results (records list) or error message.
    """
    try:
        logger.info(f"Executing ClickHouse query via MCP: {sql_query}")
        df = query_clickhouse_logic(sql_query)
        return df.to_json(orient="records", date_format="iso")
    except Exception as err:
        logger.error(f"ClickHouse query failed: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def clickhouse_table_schema(table_name: str) -> str:
    """
    Retrieves schema metadata (columns and data types) for a ClickHouse table.

    Args:
        table_name (str): Fully qualified table name, e.g. "datamart.user_sessions".

    Returns:
        str: JSON string of schema info or error message.
    """
    try:
        logger.info(f"Fetching ClickHouse schema for table: {table_name}")
        df = query_clickhouse_schema_logic(table_name)
        return df.to_json(orient="records")
    except Exception as err:
        logger.error(f"Failed to fetch ClickHouse schema: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def airflow_dags_by_dbt_table(dbt_table: str) -> str:
    """
    Retrieve all Airflow DAGs associated with a dbt table/model.

    Args:
        dbt_table (str): dbt table name (e.g. "dim_users").

    Returns:
        str: JSON-serialized mapping results.
    """
    try:
        logger.info(f"Fetching Airflow DAGs for dbt table: {dbt_table}")
        df = query_airflow_dags_by_dbt_table(dbt_table)
        return df.to_json(orient="records", date_format="iso")
    except Exception as err:
        logger.error(f"Failed to query Airflow DAGs: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def dbt_tables_by_airflow_dag(airflow_dag: str) -> str:
    """
    Retrieve all dbt tables/models associated with a specific Airflow DAG.

    Args:
        airflow_dag (str): Airflow DAG ID (e.g. "dm_user_pipeline").

    Returns:
        str: JSON-serialized mapping results.
    """
    try:
        logger.info(f"Fetching dbt tables for Airflow DAG: {airflow_dag}")
        df = query_dbt_tables_by_airflow_dag(airflow_dag)
        return df.to_json(orient="records", date_format="iso")
    except Exception as err:
        logger.error(f"Failed to query dbt tables: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})

if __name__ == "__main__":
    mcp.run(transport="streamable-http")