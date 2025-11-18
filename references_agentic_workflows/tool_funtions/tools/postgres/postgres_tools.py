# tool-functions/src/postgres_logic.py

from typing import List, Dict, Optional, Union
import pandas as pd
import logging
from utils.connector.postgres.providers import postgres_execute_query

logger = logging.getLogger(__name__)


def query_postgres_logic(sql_query: str) -> pd.DataFrame:
    """
    Executes an arbitrary SQL query on the PostgreSQL database.

    This function serves as the primary entry point for executing ad-hoc or
    dynamically generated SQL queries against a PostgreSQL database.
    The result is returned as a pandas DataFrame, making it convenient
    for analytical or programmatic processing.

    Args:
        sql_query (str): The SQL query string to execute.

    Returns:
        pd.DataFrame: Query results as a pandas DataFrame.

    Raises:
        RuntimeError: If the SQL query execution fails.

    Example:
        >>> df = query_postgres_logic("SELECT COUNT(*) FROM public.users")
        >>> print(df.head())
    """
    try:
        logger.debug(f"Executing PostgreSQL query: {sql_query}")
        return postgres_execute_query(sql_query)
    except Exception as e:
        logger.error(f"PostgreSQL query execution failed: {e}")
        raise RuntimeError(f"PostgreSQL query execution failed: {e}") from e


def query_postgres_airflow_dag_status(dag_id: str) -> Optional[Dict[str, Union[str, None]]]:
    """
    Retrieves the most recent execution status for a given Airflow DAG from Postgres metadata.

    This function queries the `public.dag_run` table to get the latest run details,
    which is useful for monitoring, debugging, or lineage validation of Airflow pipelines.

    Args:
        dag_id (str): The identifier of the Airflow DAG.

    Returns:
        Optional[Dict[str, Union[str, None]]]: A dictionary containing `dag_id`, `start_date`,
        `end_date`, and `state` of the latest DAG run. Returns `None` if no records exist.

    Raises:
        RuntimeError: If the query execution fails.

    Example:
        >>> query_airflow_dag_status("dag_notification_event")
        {'dag_id': 'dag_notification_event', 'start_date': '2025-10-25T12:30:00',
         'end_date': '2025-10-25T12:40:00', 'state': 'success'}
    """
    query = f"""
        SELECT 
            dag_id, 
            start_date, 
            end_date, 
            state
        FROM public.dag_run
        WHERE dag_id = '{dag_id}'
        ORDER BY start_date DESC
        LIMIT 1;
    """

    try:
        logger.debug(f"Querying latest Airflow DAG run for DAG ID: {dag_id}")
        df = postgres_execute_query(query)

        if df.empty:
            logger.info(f"No DAG run records found for DAG ID: {dag_id}")
            return None

        return df.iloc[0].to_dict()

    except Exception as err:
        logger.error(f"Failed to query Airflow DAG status for '{dag_id}': {err}")
        raise RuntimeError(f"Postgres query failed for DAG '{dag_id}': {err}") from err


def query_postgres_superset_clickhouse_dashboards(
    table_list: Union[str, List[str]]
) -> Union[List[Dict[str, str]], Dict[str, str], str]:
    """
    Retrieves Superset dashboards and charts associated with one or more ClickHouse tables.

    This function performs a metadata lookup from the Superset Postgres database,
    mapping ClickHouse tables to dashboards and charts that reference them.
    It supports both comma-separated strings and Python lists as input.

    Args:
        table_list (Union[str, List[str]]): A list or comma-separated string of table names.

    Returns:
        Union[List[Dict[str, str]], Dict[str, str], str]:
            - A list of dictionaries with `dashboard_name` and `chart_name` keys if matches are found.
            - A message string if no dashboards are impacted.
            - An error dictionary if the input or query fails.

    Raises:
        RuntimeError: If the SQL execution fails.

    Example:
        >>> query_superset_clickhouse_dashboards("events_dbt, user_logs_dbt")
        [
            {'dashboard_name': 'User Events Overview', 'chart_name': 'Event Count by Type'},
            {'dashboard_name': 'User Activity', 'chart_name': 'Login Frequency'}
        ]
    """
    try:
        # Normalize input
        if isinstance(table_list, str):
            tables = [t.strip().strip("'").strip('"') for t in table_list.split(",")]
        elif isinstance(table_list, list):
            tables = [str(t).strip().strip("'").strip('"') for t in table_list]
        else:
            logger.error("Invalid input type for table_list.")
            return {"status": "ERROR", "message": "Invalid input type for table_list."}

        quoted_tables = ", ".join(f"'{t}'" for t in tables)

        query = f"""
            SELECT 
                d.dashboard_title AS dashboard_name,
                s.slice_name AS chart_name
            FROM public.dashboards d
            JOIN public.dashboard_slices ds ON d.id = ds.dashboard_id
            JOIN public.slices s ON ds.slice_id = s.id
            JOIN public.tables t ON s.datasource_id = t.id AND s.datasource_type = 'table'
            JOIN public.dbs db ON t.database_id = db.id
            WHERE t.table_name IN ({quoted_tables})
        """

        logger.debug(f"Querying Superset dashboards for tables: {tables}")
        df = postgres_execute_query(query)

        if df.empty:
            logger.info(f"No impacted Superset assets found for tables: {tables}")
            return "No impacted Superset assets found for these tables."

        result_list = df[["dashboard_name", "chart_name"]].to_dict("records")
        return result_list

    except Exception as err:
        logger.error(f"Failed to query Superset dashboards: {err}")
        return {"status": "ERROR", "message": str(err)}
