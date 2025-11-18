from variables.helper import BaseConfig

class ClickHouseConfig(BaseConfig):
    """
    Configuration class for ClickHouse connection variables.

    This class inherits from `BaseConfig` and defines the required
    environment variables needed to connect to a ClickHouse database.

    Attributes
    ----------
    VARIABLES : list[str]
        A list of environment variable names required for ClickHouse setup:
        - CLICKHOUSE_HOST: Hostname or IP address of the ClickHouse server.
        - CLICKHOUSE_PORT: Port number used by the ClickHouse service.
        - CLICKHOUSE_USER: Username for database authentication.
        - CLICKHOUSE_PASSWORD: Password for database authentication.

    Example
    -------
    >> from config.clickhouse import ClickHouseConfig
    >> from variable.helper import BaseConfig, ConfigLoader
    >> ch_config = ConfigLoader.load_single(ClickHouseConfig)
    >> ch_config.get("CLICKHOUSE_HOST")
    'localhost'
    """

    VARIABLES = [
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_PORT",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD"
    ]
