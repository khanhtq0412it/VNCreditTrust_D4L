from variables.helper import BaseConfig

class PostgresConfig(BaseConfig):
    """
    Configuration class for PostgreSQL connection variables.

    This class inherits from `BaseConfig` and defines the required
    environment variables needed to establish a PostgreSQL connection.

    Attributes
    ----------
    VARIABLES : list[str]
        A list of environment variable names required for PostgreSQL setup:
        - POSTGRES_HOST: Hostname or IP address of the PostgreSQL server.
        - POSTGRES_PORT: Port number used by the PostgreSQL service.
        - POSTGRES_USER: Username for database authentication.
        - POSTGRES_PASS: Password for database authentication.
        - POSTGRES_DB_NAME: Name of the PostgreSQL database to connect to.

    Example
    -------
    >> from variable.postgres import PostgresConfig
    >> from variable.helper import BaseConfig, ConfigLoader
    >> pg_config_config = ConfigLoader.load_single(PostgresConfig)
    >> pg_config.get("POSTGRES_HOST")
    """

    VARIABLES = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASS",
        "POSTGRES_DB_NAME"
    ]
