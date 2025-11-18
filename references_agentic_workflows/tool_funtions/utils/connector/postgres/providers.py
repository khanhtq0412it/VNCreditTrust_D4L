from utils.connector.postgres.module import PostgresConnector
from variables.postgres import PostgresConfig
from variables.helper import ConfigLoader
import pandas as pd


def postgres_execute_query(query: str) -> pd.DataFrame:
    """
    Execute a SQL query on PostgreSQL and return the result as a pandas DataFrame.

    Args:
        query (str): SQL query string to execute.

    Returns:
        pd.DataFrame: Query result.

    Raises:
        RuntimeError: If the query execution fails.
    """
    try:
        # Load configuration
        postgres_config = ConfigLoader.load_single(PostgresConfig)

        # Initialize connection
        conn = PostgresConnector(
            host=postgres_config["POSTGRES_HOST"],
            port=postgres_config["POSTGRES_PORT"],
            user=postgres_config["POSTGRES_USER"],
            password=postgres_config["POSTGRES_PASS"],
            db=postgres_config["POSTGRES_DB_NAME"],
        )

        # Get SQLAlchemy engine
        engine = conn.connect_engine()

        # Execute query and return DataFrame
        df = pd.read_sql(query, engine)
        return df

    except Exception as err:
        raise RuntimeError(f"PostgreSQL query failed: {err}") from err
