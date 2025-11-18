from utils.connector.google_sheet.module import GoogleSheetClient
from typing import Optional
import pandas as pd

def fetch_google_sheet(spreadsheet_id: str, range_name: str = None, use_json_path: bool = False) -> list[list[str]]:
    """
    Fetch data from a Google Sheet using GoogleSheetClient.

    Args:
        spreadsheet_id (str): The Google Sheet ID
        range_name (str, optional): A1 notation range (e.g., 'Sheet1!A1:D100').
                                    Defaults to 'Sheet1' if not provided.
        use_json_path (bool, optional): If True, authenticate using JSON file path.
                                        Defaults to False (use JSON string).

    Returns:
        list[list[str]]: Sheet values as list of rows
    """
    # Default range
    if range_name is None:
        range_name = "Trang tính1"

    client = GoogleSheetClient(use_json_path=use_json_path)
    return client.read_sheet(spreadsheet_id, range_name)

def fetch_google_sheet_as_df(spreadsheet_id: str,
                             range_name: Optional[str] = None,
                             use_json_path: bool = False,
                             header: bool = True) -> pd.DataFrame:
    """
    Fetch Google Sheet data and return as pandas DataFrame.

    Args:
        spreadsheet_id (str): Google Sheet ID
        range_name (str, optional): A1 notation range (e.g., 'Sheet1!A1:D100').
                                    Defaults to None -> Sheet1
        use_json_path (bool, optional): If True, authenticate using JSON file path.
        header (bool, optional): If True, use first row as column names. Default True.

    Returns:
        pd.DataFrame: Sheet values as DataFrame
    """
    data = fetch_google_sheet(spreadsheet_id, range_name=range_name, use_json_path=use_json_path)

    if not data:
        return pd.DataFrame()  # empty DataFrame

    if header:
        # first row as column names
        df = pd.DataFrame(data[1:], columns=data[0])
    else:
        df = pd.DataFrame(data)

    return df

def get_google_sheet_names(spreadsheet_id: str, use_json_path: bool = False) -> list[str]:
    """
    Fetch all sheet (tab) names from a Google Spreadsheet.

    Args:
        spreadsheet_id (str): Google Sheet ID
        use_json_path (bool): Authenticate via JSON file path if True

    Returns:
        list[str]: List of sheet names
    """
    client = GoogleSheetClient(use_json_path=use_json_path)

    # access spreadsheet metadata
    try:
        response = (
            client.service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id)
            .execute()
        )

        sheets = response.get("sheets", [])
        sheet_names = [s["properties"]["title"] for s in sheets]

        return sheet_names

    except Exception as err:
        print(f"Failed to fetch sheet names: {err}")
        return []

def get_google_sheet_title(spreadsheet_id: str, use_json_path: bool = False) -> str:
    """
    Retrieve the title (file name) of a Google Spreadsheet.

    Args:
        spreadsheet_id (str): The unique Google Spreadsheet ID.
        use_json_path (bool, optional): If True, authenticate using a JSON file path
                                        instead of a JSON string. Defaults to False.

    Returns:
        str: The title of the Google Sheet. Returns an empty string if retrieval fails.
    """
    client = GoogleSheetClient(use_json_path=use_json_path)

    try:
        response = (
            client.service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id)
            .execute()
        )

        return response.get("properties", {}).get("title", "")

    except Exception as err:
        print(f"Failed to fetch sheet title: {err}")
        return ""
