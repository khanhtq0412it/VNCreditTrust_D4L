import json
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from variables.google_sheet import GoogleSheetConfig
from variables.helper import ConfigLoader

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GoogleSheetClient:
    """
    Client class to authenticate and read data from Google Sheets.

    Authentication priority:
      1. GOOGLE_SHEET_SERVICE_ACCOUNT (JSON string, default)
      2. GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH (file path, if use_json_path=True)
    """

    def __init__(self, use_json_path: bool = False):
        gs_config = ConfigLoader.load_single(GoogleSheetConfig)

        sa_json_str = gs_config.get("GOOGLE_SHEET_SERVICE_ACCOUNT", None)
        sa_json_path = gs_config.get("GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH", None)

        if use_json_path:
            if sa_json_path:
                self.credentials = Credentials.from_service_account_file(
                    sa_json_path,
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
                )
                logger.info(f"Using GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH: {sa_json_path}")
            else:
                raise ValueError("Flag use_json_path=True but GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH not set.")
        else:
            if sa_json_str:
                self.credentials = Credentials.from_service_account_info(
                    json.loads(sa_json_str),
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
                )
                logger.info("Using GOOGLE_SHEET_SERVICE_ACCOUNT (JSON string) for authentication.")
            elif sa_json_path:
                # fallback nếu JSON string không có
                self.credentials = Credentials.from_service_account_file(
                    sa_json_path,
                    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
                )
                logger.info(f"Fallback to GOOGLE_SHEET_SERVICE_ACCOUNT_JSON_PATH: {sa_json_path}")
            else:
                raise ValueError("No Google Sheet credentials provided via env variables.")

        self.service = build("sheets", "v4", credentials=self.credentials)
        self.sheet = self.service.spreadsheets()

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        """
        Read sheet values (sync).

        Args:
            spreadsheet_id (str): Google Sheet ID
            range_name (str): Range in A1 notation (e.g., "Sheet1!A1:D100")

        Returns:
            list[list[str]]: Sheet values
        """
        try:
            logger.info(f"Reading Google Sheet {spreadsheet_id}, range {range_name}")
            result = self.sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get("values", [])
        except Exception as err:
            logger.error(f"Failed to read Google Sheet: {err}")
            raise
