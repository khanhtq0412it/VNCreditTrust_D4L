import pandas as pd
from utils.connector.clickhouse.helper import connect_to_clickhouse
from variables.clickhouse import ClickHouseConfig
from variables.helper import ConfigLoader


def clickhouse_execute_query(query: str) -> pd.DataFrame:
    """
    Execute an SQL query on ClickHouse and return the result as a pandas DataFrame.

    This function loads ClickHouse connection settings from environment variables,
    establishes a connection, runs the provided SQL query, and converts the result
    into a pandas DataFrame for further analysis or processing.

    Args:
        query (str): The SQL query to execute on the ClickHouse database.

    Returns:
        pd.DataFrame: Query result as a DataFrame containing rows and column names.

    Raises:
        RuntimeError: If the query execution or database connection fails.

    Example:
        >> query = "SELECT * FROM analytics.events LIMIT 10"
        >> df = clickhouse_execute_query(query)
        >> print(df.head())
    """
    try:
        # Load configuration and establish a ClickHouse connection
        clickhouse_config = ConfigLoader.load_single(ClickHouseConfig)
        conn = connect_to_clickhouse(clickhouse_config)
        client = conn.connect_client()

        # Execute the query
        result = client.query(query)
        rows = result.result_rows
        columns = result.column_names

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)
        return df

    except Exception as err:
        raise RuntimeError(f"ClickHouse query failed: {err}") from err
