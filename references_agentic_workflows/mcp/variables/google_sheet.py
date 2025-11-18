from variables.helper import BaseConfig

class GoogleSheetConfig(BaseConfig):
    """
    Configuration class for Google Sheet access variables.

    This class inherits from `BaseConfig` and defines the required
    environment variables needed to authenticate with Google Sheets.

    Attributes
    ----------
    VARIABLES : list[str]
        - GOOGLE_SERVICE_ACCOUNT_JSON_PATH: Path to service_account.json file.
        - GOOGLE_SERVICE_ACCOUNT: Optional. JSON string of service account content.

    Example
    -------
    >> from config.google_sheet import GoogleSheetConfig
    >> from variables.helper import ConfigLoader
    >> gs_config = ConfigLoader.load_single(GoogleSheetConfig)
    >> gs_config.get("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    '/opt/credentials/service_account.json'
    """

    VARIABLES = [
        "GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH",
        "GOOGLE_SHEET_SERVICE_ACCOUNT"
    ]
