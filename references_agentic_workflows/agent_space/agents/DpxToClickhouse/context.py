import sys
from pathlib import Path
import asyncio
from variables.helper import ConfigLoader
from variables.agentspaces.dpx2clickhouse import Dpx2Clickhouse

# --- Repo root for local imports ---
REPO_ROOT = str(Path(__file__).resolve().parents[2])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Optional wrappers
try:
    from utils.llm.gemini.module import GeminiLLM
except Exception:
    GeminiLLM = None

try:
    from framework.mcp_adapters.server import MCPClientWrapper
except Exception:
    MCPClientWrapper = None

# Config
dpx2clickhouse_config = ConfigLoader.load_single(Dpx2Clickhouse)


# Initialize LLMs
def init_llm():
    return GeminiLLM().get_llm() if GeminiLLM else None


llm_google_sheet = init_llm()
llm_gitlab_vetc = init_llm()
llm_orchestrator = init_llm()
llm_summary = init_llm()

# MCP client & tools
mcp = MCPClientWrapper() if MCPClientWrapper else None
tools_google_sheet_query, tools_gitlab_vetc = [], []


async def discover_tools():
    global tools_google_sheet_query, tools_gitlab_vetc
    if not mcp:
        return
    try:
        gs_tools = await mcp.aget_tools(server_name='google_sheet-server', tool_name='google_sheet_query')
        tools_google_sheet_query = gs_tools if isinstance(gs_tools, list) else [gs_tools]
    except Exception:
        tools_google_sheet_query = []

    try:
        git_tools = await mcp.aget_tools(server_name='gitlab_vetc-server')
        tools_gitlab_vetc = git_tools if isinstance(git_tools, list) else [git_tools]
    except Exception:
        tools_gitlab_vetc = []


# Run discovery at import time (fast-fail if mcp missing)
try:
    asyncio.run(discover_tools())
except Exception:
    # ignore async discovery failures at import time
    pass

# Bind tools to LLMs
for llm in [llm_google_sheet, llm_orchestrator, llm_gitlab_vetc]:
    if llm and tools_google_sheet_query:
        try:
            llm.bind_tools(tools_google_sheet_query)
            llm.bind_tools(tools_gitlab_vetc)
        except Exception:
            pass

# Output file paths
output_dir = None
