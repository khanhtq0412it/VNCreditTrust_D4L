import asyncio
import json
import os
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
import context as ctx
from typing import List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from utils.common.prompt.prompt_loader import load_prompt_file, render_prompt
from utils.common.function.gitlab_helpers import get_dbt_model_logic, get_dbt_model_schema


class MigrationState(BaseModel):
    """
    State object for the DPX → ClickHouse migration agent.
    Stores workflow messages, intermediate results, and final output.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ============================================================
    # 1. Orchestrator-bound messages (LangGraph uses this field)
    # ============================================================
    messages: List[BaseMessage] = Field(
        default_factory=list,
        json_schema_extra={"add_messages": add_messages}
    )


    # ============================================================
    # 2. Sheet IDs (input identifiers)
    # ============================================================
    mapping_sheet_id: Optional[str] = None
    pii_sheet_id: Optional[str] = None

    # ---------------------------------------------------------
    # 3. Loaded sheet contents
    # ---------------------------------------------------------
    mapping_sheet_data: Any = None
    pii_sheet_data: Any = None

    # ---------------------------------------------------------
    # 4. Resolved table identifiers (from text extraction)
    # ---------------------------------------------------------
    clickhouse_stg_table: Optional[str] = None      # staging table
    clickhouse_raw_table: Optional[str] = None      # raw table

    dpx_catalog: Optional[str] = None
    dpx_schema: Optional[str] = None                # namespace → schema
    dpx_table_name: Optional[str] = None
    dpx_table_id: Optional[str] = None

    # ---------------------------------------------------------
    # 5. Metadata: PII + schema info
    # ---------------------------------------------------------
    stg_pii_columns: Optional[List[str]] = None
    stg_table_schema: Optional[str] = None          # extracted schema

    # ---------------------------------------------------------
    # 6. GitLab SQL logic (fetched source definitions)
    # ---------------------------------------------------------
    stg_sql_logic: Optional[str] = None             # staging ClickHouse logic
    raw_sql_logic: Optional[str] = None             # raw ClickHouse logic
    dpx_sql_logic: Optional[str] = None             # DPX table logic

    # ---------------------------------------------------------
    # 7. Additional external paths
    # ---------------------------------------------------------
    minio_s3_path: Optional[str] = None

    # ---------------------------------------------------------
    # 8. Final orchestrator outputs
    # ---------------------------------------------------------
    generated_stg_dbt_model: Optional[str] = None         # new .sql
    generated_stg_schema_yaml: Optional[str] = None       # new yaml

    # ---------------------------------------------------------
    # 9. Control flags
    # ---------------------------------------------------------
    is_orchestrator_ready: bool = False


# Node implementations (adapted from previous agent.py)

def orchestrator_node(state: MigrationState) -> MigrationState:
    if not state.is_orchestrator_ready:
        state.mapping_sheet_id = ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_MAPPING_STAGING_TO_DPX_SHEET']
        state.pii_sheet_id = ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_PII_COLUMNS_SHEET']
        state.is_orchestrator_ready = True

    pr_tpl = load_prompt_file("prompts.md", "Step for agent to follow")
    pr_tpl_render = render_prompt(
        pr_tpl,
        {
            "mapping_sheet_id": state.mapping_sheet_id,
            "pii_sheet_id": state.pii_sheet_id,
        }
    )
    state.messages.append(SystemMessage(content=pr_tpl_render))
    return state


def extract_stg_table_node(state: MigrationState) -> MigrationState:
    user_text = " ".join(msg.content for msg in state.messages if isinstance(msg, HumanMessage))
    llm = ctx.llm_google_sheet or (ctx.llm_orchestrator if ctx.llm_orchestrator else None)

    if llm:
        pr_tpl = load_prompt_file("prompts.md", "Extract Staging ClickHouse Table")
        pr_tpl_render = render_prompt(
            pr_tpl,
            {
                "user_text": user_text,
            }
        )
        response = llm.invoke(pr_tpl_render)
        state.clickhouse_stg_table = str(response.content).strip().strip('`')
        state.messages.append(SystemMessage(content=f"LLM extracted clickhouse_stg_table: `{state.clickhouse_stg_table}`"))
    else:
        state.clickhouse_stg_table = user_text.strip().split()[-1]

    return state


def query_google_sheet(state: MigrationState, sheet_id_attr: str):
    if not getattr(state, sheet_id_attr):
        raise ValueError(f"{sheet_id_attr} missing in state")
    sheet_id = getattr(state, sheet_id_attr)
    payload = {"spreadsheet_id": sheet_id}

    result = asyncio.run(ctx.mcp.aexecute_tool("google_sheet-server", "google_sheet_query", payload)) if ctx.mcp else []
    if isinstance(result, str):
        try:
            data = json.loads(result)
        except Exception:
            data = []
    elif isinstance(result, list):
        data = result
    else:
        data = []

    target_name = state.clickhouse_stg_table
    matched = [row for row in data if
               str(row.get("clickhouse_stg_table", "")).strip().lower() == target_name.lower()]
    return matched[0] if matched else None, data

def query_mapping_stg_dpx_node(state: MigrationState) -> MigrationState:
    row, _ = query_google_sheet(state, "mapping_sheet_id")
    if not row:
        raise ValueError(f"No mapping found for staging table '{state.clickhouse_stg_table}'")
    state.clickhouse_raw_table = row.get("clickhouse_raw_table")
    state.dpx_catalog = row.get("dpx_catalog")
    state.dpx_schema = row.get("dpx_schema")
    state.dpx_table_name = row.get("dpx_table_name")
    state.dpx_table_id = row.get("dpx_table_id")
    state.mapping_sheet_data = row
    state.messages.append(SystemMessage(content=f"Found mapping: {row}"))
    return state


def query_pii_node(state: MigrationState) -> MigrationState:
    row, _ = query_google_sheet(state, "pii_sheet_id")
    pii_cols = []
    if row:
        raw_cols = row.get("stg_pii_columns", [])
        if isinstance(raw_cols, str):
            pii_cols = [raw_cols.strip()] if raw_cols.strip() else []
        elif isinstance(raw_cols, list):
            pii_cols = [str(x).strip() for x in raw_cols]
    state.stg_pii_columns = pii_cols
    state.pii_sheet_data = row
    state.messages.append(SystemMessage(content=f"Found PII columns: {pii_cols}"))
    return state


def extract_s3_path_node(state: MigrationState) -> MigrationState:
    if not state.dpx_table_id:
        raise ValueError("dpx_table_id missing in state")
    sql = f"select fs_location from public.active_tables where table_id = '{state.dpx_table_id}'"
    payload = {"sql_query": sql}
    result = asyncio.run(ctx.mcp.aexecute_tool("airflow_postgres_gcp-server", "postgres_query", payload)) if ctx.mcp else '[]'
    try:
        state.minio_s3_path = "https://s3-dpex.vetc.com.vn/" + json.loads(result)[0]['fs_location']
    except Exception:
        state.minio_s3_path = None
    state.messages.append(SystemMessage(content=f"Extracted S3 MinIO path: {state.minio_s3_path}"))
    return state


async def fetch_clickhouse_schema(state: MigrationState) -> MigrationState:
    if not state.stg_table_schema:
        state.stg_table_schema = await get_dbt_model_schema(
            ctx.mcp,
            state.clickhouse_stg_table,
            project_id=ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO'],
        )
        state.messages.append(SystemMessage(content=f"[GetDBTClickhouseSchema] Retrieved schema for `{state.clickhouse_stg_table}`"))
    return state


async def fetch_dbt_logic(state: MigrationState) -> MigrationState:
    if all([state.stg_sql_logic, state.raw_sql_logic, state.dpx_sql_logic]):
        return state

    if not ctx.llm_gitlab_vetc:
        state.messages.append(SystemMessage(content="[QueryGitlabDBT] No llm_gitlab_vetc available"))
        return state

    required_fields = [state.clickhouse_stg_table, state.clickhouse_raw_table, state.dpx_table_name,
                       state.dpx_catalog, state.dpx_schema, state.dpx_table_id]
    if all(required_fields):
        state.stg_sql_logic = await get_dbt_model_logic(
            ctx.mcp,
            model_name=state.clickhouse_stg_table,
            project_id=ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO'],
            path='models/staging',
        )
        state.raw_sql_logic = await get_dbt_model_logic(
            ctx.mcp,
            model_name=state.clickhouse_raw_table,
            project_id=ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_DBT_CLICKHOUSE_REPO'],
            path='models/raw',
        )
        state.dpx_sql_logic = await get_dbt_model_logic(
            ctx.mcp,
            model_name=state.dpx_table_name,
            project_id=ctx.dpx2clickhouse_config['DPX2CLICKHOUSE_DBT_TRINO_REPO'],
            path=f'models/{state.dpx_catalog}/{state.dpx_schema}',
            ref='production',
        )
        state.messages.append(SystemMessage(content="[QueryGitlabDBT] Retrieved dbt logic for ClickHouse and DPX tables"))
    else:
        state.messages.append(SystemMessage(content="[QueryGitlabDBT] Missing required fields to fetch dbt logic"))
    return state


async def summarize_migration_node(state: MigrationState) -> MigrationState:
    if not ctx.llm_summary:
        state.messages.append(SystemMessage(content="[Summary] No llm_summary available"))
        return state

    # load prompt template and render with state values
    mapping = {
        "clickhouse_stg_table": state.clickhouse_stg_table or "",
        "stg_sql_logic": state.stg_sql_logic or "",
        "raw_sql_logic": state.raw_sql_logic or "",
        "dpx_sql_logic": state.dpx_sql_logic or "",
        "minio_s3_path": state.minio_s3_path or "",
        "stg_table_schema": state.stg_table_schema or "",
        "stg_pii_columns": ", ".join(state.stg_pii_columns or []),
    }

    pr_tpl = load_prompt_file("prompts.md", "Summarize and Rewrite Staging DBT Logic & YAML")
    pr_tpl_render = render_prompt(
        pr_tpl,
        mapping
    )
    raw_response = ctx.llm_summary.invoke(pr_tpl_render).content.strip()
    state.messages.append(SystemMessage(content="[Summary] Raw LLM response:"))

    try:
        cleaned = raw_response.strip("```json").strip("```").strip()
        rs_json = json.loads(cleaned)
        state.generated_stg_dbt_model = rs_json.get("generated_stg_dbt_model")
        state.generated_stg_schema_yaml = rs_json.get("generated_stg_schema_yaml")
        state.messages.append(SystemMessage(content="[Summary] Successfully parsed new logic + schema"))
    except json.JSONDecodeError as e:
        state.messages.append(SystemMessage(content=f"[Summary] JSON decode error: {e}\nRaw response:\n{raw_response}"))
    return state


def write_output_node(state: MigrationState) -> MigrationState:
    if not state.generated_stg_dbt_model or not state.generated_stg_schema_yaml:
        state.messages.append(SystemMessage(content="[WriteOutputFiles] Missing logic or schema to write"))
        return state

    if ctx.output_dir:
        output_dir = os.path.join(ctx.output_dir, 'output_files')
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.join(os.path.dirname(__file__), 'output_files')
        os.makedirs(output_dir, exist_ok=True)

    sql_file = os.path.join(output_dir, f"dpx_{state.clickhouse_stg_table}.sql")
    yaml_file = os.path.join(output_dir, f"dpx_{state.clickhouse_stg_table}_schema.yaml")

    with open(sql_file, "w", encoding="utf-8") as f:
        f.write(state.generated_stg_dbt_model)
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(state.generated_stg_schema_yaml)

    state.messages.append(SystemMessage(content=f"[WriteOutputFiles] Wrote files:\n- SQL: {sql_file}\n- YAML: {yaml_file}"))
    return state

# router is built in agentic/graph.py
