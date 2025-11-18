# tool-functions/src/google_sheet_logic.py

import pandas as pd
import logging
from typing import Optional, List

from utils.connector.google_sheet.providers import (
    fetch_google_sheet_as_df,
    get_google_sheet_names,
    get_google_sheet_title,
)

logger = logging.getLogger(__name__)


def query_google_sheet_data(
    spreadsheet_id: str,
    range_name: Optional[str] = None,
    use_json_path: bool = False,
    header: bool = True
) -> pd.DataFrame:
    """
    Reads a specific range of values from a Google Sheet and returns a DataFrame.

    This function is the primary entry point for interacting with spreadsheet
    tabular data stored in Google Sheets. It is commonly used by LLM agents
    or automation scripts to extract structured information.

    Args:
        spreadsheet_id (str):
            The Google Spreadsheet ID (from URL).
        range_name (str, optional):
            The A1-notation range to read, e.g. "Sheet1!A1:D100".
            Defaults to None (sheet default).
        use_json_path (bool, optional):
            If True, authenticate using Google credential JSON file path.
            Otherwise expects JSON string in an environment variable.
        header (bool, optional):
            Automatic first-row column headers. Defaults to True.

    Returns:
        pd.DataFrame: DataFrame containing sheet data.

    Raises:
        RuntimeError: If Sheet read fails.

    Example:
        >>> df = query_google_sheet_data("1Hmd...", "Sheet1!A1:D100")
        >>> print(df.head())
    """
    try:
        logger.debug(
            f"[GoogleSheet] Reading spreadsheet={spreadsheet_id}, range={range_name}"
        )
        return fetch_google_sheet_as_df(
            spreadsheet_id,
            range_name=range_name,
            use_json_path=use_json_path,
            header=header
        )
    except Exception as e:
        logger.error(f"[GoogleSheet] Fetch failed: {e}")
        raise RuntimeError(f"Google Sheet query failed: {e}") from e


def query_google_sheet_tabs(
    spreadsheet_id: str,
    use_json_path: bool = False
) -> List[str]:
    """
    Retrieves all tab (sheet) names available in a Google Spreadsheet.

    Useful for introspection, agent prompting, and multi-sheet workflows.

    Args:
        spreadsheet_id (str):
            The Google Spreadsheet ID.
        use_json_path (bool, optional):
            Use JSON file path to authenticate. Defaults False.

    Returns:
        list[str]: Names of tabs inside the Google Spreadsheet.

    Example:
        >>> query_google_sheet_tabs("1Hmd...")
        ['Sheet1', 'Config', 'Mapping']
    """
    try:
        logger.debug(f"[GoogleSheet] Fetching sheet names: {spreadsheet_id}")
        return get_google_sheet_names(spreadsheet_id, use_json_path)
    except Exception as e:
        logger.error(
            f"[GoogleSheet] Unable to list sheet tabs: {e}"
        )
        raise RuntimeError(
            f"Failed to retrieve sheet tabs for '{spreadsheet_id}': {e}"
        ) from e


def query_google_sheet_title_logic(
    spreadsheet_id: str,
    use_json_path: bool = False
) -> str:
    """
    Retrieve the Google Sheet file (document) title.

    This helps metadata pipelines map document-level lineage
    or annotate output artifacts with human-readable labels.

    Args:
        spreadsheet_id (str):
            Google Spreadsheet ID.
        use_json_path (bool, optional):
            Authenticate using credential JSON file path.

    Returns:
        str: File title.

    Example:
        >>> query_google_sheet_title_logic("1Hmd...")
        'Timeline Project'
    """
    try:
        logger.debug(f"[GoogleSheet] Fetching sheet title: {spreadsheet_id}")
        return get_google_sheet_title(spreadsheet_id, use_json_path)
    except Exception as e:
        logger.error(f"[GoogleSheet] Failed to fetch title: {e}")
        raise RuntimeError(
            f"Failed to retrieve sheet title for '{spreadsheet_id}': {e}"
        ) from e
