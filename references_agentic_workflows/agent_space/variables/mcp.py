from variables.helper import BaseConfig

class MCPConfig(BaseConfig):
    """
    Configuration loader for MCP (Model Context Protocol) servers used to expose
    external resources such as databases to agentic runtimes.

    This class inherits from `BaseConfig` and defines the required environment
    variables that specify the connection URLs for MCP-compatible backend
    servers. These servers are used by agents to retrieve contextual data such
    as workflow status, metadata, or analytics without embedding credentials
    directly into the agent runtime.

    Attributes
    ----------
    VARIABLES : list[str]
        List of required configuration variable keys:
        - "MCP_SERVER_AIRFLOW_POSTGRES_GCP_URL": MCP endpoint that provides
          access to the Airflow Postgres database hosted on Google Cloud.
          Typically used to query DAG execution metadata and run status.
        - "MCP_SERVER_CLICKHOUSE_GCP_URL": MCP endpoint that exposes the
          ClickHouse data warehouse on Google Cloud for real-time analytics or
          query-based reasoning.
    """
    VARIABLES = [
        "MCP_SERVER_AIRFLOW_POSTGRES_GCP_URL",
        "MCP_SERVER_CLICKHOUSE_GCP_URL",
        "MCP_SERVER_GOOGLE_SHEET_URL",
        "MCP_SERVER_GITLAB_VETC_URL"
    ]
