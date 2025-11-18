# tool-functions/src/clickhouse_logic.py

import pandas as pd
from utils.connector.clickhouse.providers import clickhouse_execute_query
import logging

logger = logging.getLogger(__name__)


def query_clickhouse_logic(sql_query: str) -> pd.DataFrame:
    """
    Executes an arbitrary SQL query on ClickHouse.

    This is the primary entry point for executing ad-hoc or dynamic SQL queries
    against the ClickHouse database. The result is returned as a pandas DataFrame.

    Args:
        sql_query (str): The SQL query string to execute.

    Returns:
        pd.DataFrame: Query results as a DataFrame.

    Raises:
        RuntimeError: If the query execution fails.

    Example:
        >>> df = query_clickhouse_logic("SELECT count(*) FROM events_dbt")
        >>> print(df.head())
    """
    try:
        logger.debug(f"Executing ClickHouse query: {sql_query}")
        return clickhouse_execute_query(sql_query)
    except Exception as e:
        logger.error(f"ClickHouse query execution failed: {e}")
        raise RuntimeError(f"ClickHouse query execution failed: {e}") from e


def query_clickhouse_schema_logic(table_name: str) -> pd.DataFrame:
    """
    Retrieves column metadata (name and data type) for a specific ClickHouse table.

    This function queries the `system.columns` table to extract schema information.
    It is particularly useful for:
      - Large Language Model (LLM) agents generating SQL dynamically,
      - Automated schema validation,
      - Data model introspection in analytics pipelines.

    Args:
        table_name (str): Name of the ClickHouse table to inspect.

    Returns:
        pd.DataFrame: A DataFrame containing the columns `column_name` and `data_type`.

    Example:
        >>> query_clickhouse_schema_logic("events_dbt")
        column_name  data_type
        user_id      UInt64
    """
    query = f"""
        SELECT 
            name AS column_name,
            type AS data_type
        FROM system.columns
        WHERE table = '{table_name}'
        ORDER BY position
    """
    try:
        logger.debug(f"Fetching schema for table: {table_name}")
        return clickhouse_execute_query(query)
    except Exception as e:
        logger.error(f"Failed to retrieve schema for table '{table_name}': {e}")
        raise RuntimeError(f"Schema query failed for table '{table_name}': {e}") from e


def query_dbt_tables_by_airflow_dag(airflow_dag: str) -> pd.DataFrame:
    """
    Retrieve dbt model tables associated with a specific Airflow DAG.

    This function provides metadata lineage between the orchestration layer
    (Airflow DAG) and the transformation layer (dbt models). It enables faster
    debugging, lineage tracing, and metadata-driven automation workflows.

    Args:
        airflow_dag (str):
            The Airflow DAG identifier used for querying the metadata mapping.

    Returns:
        pd.DataFrame:
            A DataFrame containing one or more rows, each representing a dbt
            model referenced by the given Airflow DAG. The DataFrame includes
            a `dbt_table` column.

    Raises:
        RuntimeError:
            If the metadata lookup fails due to query execution issues.

    Example:
        >> get_dbt_tables_by_airflow_dag("dag_notification_event")
              dbt_table
        0     events_dbt
    """
    query = f"""
        SELECT dbt_table
        FROM staging_dev.airflow_clickhouse_table_mapping
        WHERE airflow_dag = '{airflow_dag}'
    """

    try:
        logger.debug(f"[Metadata] Fetching dbt_table for DAG: {airflow_dag}")
        return clickhouse_execute_query(query)
    except Exception as e:
        logger.error(f"[Metadata] Failed: DAG='{airflow_dag}' → {e}")
        raise RuntimeError(
            f"Metadata lookup failed for DAG '{airflow_dag}': {e}"
        ) from e

def query_airflow_dags_by_dbt_table(table_name: str) -> pd.DataFrame:
    """
    Retrieve Airflow DAGs that produce or reference a specific dbt model table.

    This function supports downstream lineage investigations, allowing engineers
    to determine which Airflow pipeline is responsible for building or updating
    a given dbt model. It is useful for debugging data freshness, failures, and
    ETL dependency tracking.

    Args:
        table_name (str):
            The dbt model or target warehouse table used in lineage mapping.

    Returns:
        pd.DataFrame:
            A DataFrame containing one or more rows, each representing an
            Airflow DAG associated with the specified table. The DataFrame
            includes an `airflow_dag` column.

    Raises:
        RuntimeError:
            If the metadata lookup fails due to query execution issues.

    Example:
        >> get_airflow_dags_by_dbt_table("events_dbt")
              airflow_dag
        0     dag_notification_event
    """
    query = f"""
        SELECT airflow_dag
        FROM staging_dev.airflow_clickhouse_table_mapping
        WHERE dbt_table = '{table_name}'
    """

    try:
        logger.debug(f"[Metadata] Fetching airflow_dag for table: {table_name}")
        return clickhouse_execute_query(query)
    except Exception as e:
        logger.error(f"[Metadata] Failed: dbt_table='{table_name}' → {e}")
        raise RuntimeError(
            f"Metadata lookup failed for table '{table_name}': {e}"
        ) from e
