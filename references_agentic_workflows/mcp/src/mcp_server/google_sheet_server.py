"""
Google Sheet MCP Server
=======================

This module defines a production-grade MCP (Modular Control Protocol) server
for Google Sheets. It enables external agents or orchestration systems to:

Available Tools:
    1. `google_sheet_query` — Read sheet tabular data.
    2. `google_sheet_tabs` — List all sheet (tab) names.
    3. `google_sheet_title` — Retrieve the file (document) title.

Usage:
    $ python mcp_google_sheet_server.py
"""

import asyncio
import json
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from tools.google_sheet.google_sheet_tools import (
    query_google_sheet_data,
    query_google_sheet_tabs,
    query_google_sheet_title_logic,
)

# ---------------------------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# MCP Server Initialization
# ---------------------------------------------------------------------------
mcp = FastMCP("Google Sheet MCP Server", host="0.0.0.0", port=8082)

# ---------------------------------------------------------------------------
# MCP Tools Registration
# ---------------------------------------------------------------------------


@mcp.tool()
async def google_sheet_query(
    spreadsheet_id: str,
    range_name: Optional[str] = None,
    use_json_path: bool = False,
    header: bool = True
) -> str:
    """
    Reads a defined range from a Google Sheet and returns structured data.

    Args:
        spreadsheet_id (str): The Google Spreadsheet ID (from sheet URL).
        range_name (str, optional): A1 notation (e.g., "Sheet1!A1:D50").
        use_json_path (bool, optional): Authenticate via JSON credential file path.
        header (bool, optional): Treat first row as headers.

    Returns:
        str: JSON-serialized rows list.

    Example:
        >>> google_sheet_query("1Hmd...", "Data!A1:C100")
    """
    try:
        logger.info(f"[MCP] Reading Google Sheet: {spreadsheet_id}, range={range_name}")
        df = query_google_sheet_data(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            use_json_path=use_json_path,
            header=header
        )
        return df.to_json(orient="records", date_format="iso")
    except Exception as err:
        logger.error(f"[MCP] Google Sheet read failed: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def google_sheet_tabs(
    spreadsheet_id: str,
    use_json_path: bool = False
) -> str:
    """
    Retrieves a list of sheet (tab) names within a Google Spreadsheet.

    Args:
        spreadsheet_id (str): Google Spreadsheet ID.
        use_json_path (bool, optional): Authenticate via JSON file path.

    Returns:
        str: JSON array of sheet names.

    Example:
        >>> google_sheet_tabs("1Hmd...")
        ["Sheet1", "Config", "Mapping"]
    """
    try:
        logger.info(f"[MCP] Fetching sheet tabs from: {spreadsheet_id}")
        tabs = query_google_sheet_tabs(spreadsheet_id, use_json_path)
        return json.dumps(tabs)
    except Exception as err:
        logger.error(f"[MCP] Failed to fetch sheet tabs: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


@mcp.tool()
async def google_sheet_title(
    spreadsheet_id: str,
    use_json_path: bool = False
) -> str:
    """
    Retrieves the Google Sheet file title.

    Args:
        spreadsheet_id (str): Google Spreadsheet ID.
        use_json_path (bool, optional): Authenticate via JSON file path.

    Returns:
        str: JSON string containing the title.

    Example:
        >>> google_sheet_title("1Hmd...")
        "Timeline Project"
    """
    try:
        logger.info(f"[MCP] Fetching sheet title for: {spreadsheet_id}")
        title = query_google_sheet_title_logic(spreadsheet_id, use_json_path)
        return json.dumps({"title": title})
    except Exception as err:
        logger.error(f"[MCP] Failed to fetch sheet title: {err}")
        return json.dumps({"status": "ERROR", "message": str(err)})


# ---------------------------------------------------------------------------
# Run Server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
