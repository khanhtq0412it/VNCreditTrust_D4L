from variables.helper import BaseConfig

class Dpx2Clickhouse(BaseConfig):
    """

    """
    VARIABLES = [
        "DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET",
        "DPX2CLICKHOUSE_PII_COLUMNS_SHEET",
        "DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO",
        "DPX2CLICKHOUSE_DBT_TRINO_REPO",
    ]
