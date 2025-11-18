# ============================================================
# Professional Runnable Agentic Graph for DPX → ClickHouse
# ============================================================

from pathlib import Path
import sys

# Ensure repository root is in sys.path (absolute imports)
REPO_ROOT = str(Path(__file__).resolve().parents[3])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import workflow node implementations
from agents.DpxToClickhouse.node_functions import (
    MigrationState,
    orchestrator_node,
    extract_stg_table_node,
    query_mapping_stg_dpx_node,
    query_pii_node,
    fetch_dbt_logic,
    extract_s3_path_node,
    fetch_clickhouse_schema,
    summarize_migration_node,
    write_output_node,
)

from langgraph.graph import StateGraph, START, END


# ============================================================
# Node Name Constants
# ============================================================
NODES = {
    "Orchestrator": orchestrator_node,
    "ExtractStagingTable": extract_stg_table_node,
    "QueryMapping": query_mapping_stg_dpx_node,
    "QueryPII": query_pii_node,
    "QueryGitlabDBTLogic": fetch_dbt_logic,
    "ExtractS3Path": extract_s3_path_node,
    "FetchSchema": fetch_clickhouse_schema,
    "SummarizeMigration": summarize_migration_node,
    "WriteOutput": write_output_node,
}

NODE_ORDER = list(NODES.keys())


# ============================================================
# Router Function (Main State Machine)
# ============================================================
def workflow_router(state: MigrationState) -> str:

    # 1. Extract staging CH table
    if not state.clickhouse_stg_table:
        return "ExtractStagingTable"

    # 2. Load mapping sheet
    if not state.mapping_sheet_data:
        return "QueryMapping"

    # 3. Load PII sheet
    if not state.pii_sheet_data:
        return "QueryPII"

    # 4. DBT logic from GitLab
    if not (
        state.stg_sql_logic
        and state.raw_sql_logic
        and state.dpx_sql_logic
    ):
        return "QueryGitlabDBTLogic"

    # 5. Extract S3 MinIO path
    if not state.minio_s3_path:
        return "ExtractS3Path"

    # 6. Fetch staging ClickHouse schema
    if not state.stg_table_schema:
        return "FetchSchema"

    # 7. Summarize → generate new dbt.sql + schema.yaml
    if not (state.generated_stg_dbt_model and state.generated_stg_schema_yaml):
        return "SummarizeMigration"

    # 8. Finally write output files
    return "WriteOutput"


# ============================================================
# Build the Graph
# ============================================================
workflow = StateGraph(MigrationState)

# Add all nodes
for name, func in NODES.items():
    workflow.add_node(name, func)

# Entry point
workflow.add_edge(START, "Orchestrator")

# Conditional routing from Orchestrator
workflow.add_conditional_edges("Orchestrator", workflow_router, NODE_ORDER)

# Each node returns back to Orchestrator for next decision
for name in NODES:
    if name != "WriteOutput" and name != "Orchestrator" and name != "SummarizeMigration":
        workflow.add_edge(name, "Orchestrator")

# Terminal edges
workflow.add_conditional_edges(
    "SummarizeMigration",
    workflow_router,
    ["WriteOutput", END]
)

app = workflow.compile()


# ============================================================
# Optional Runner for Debugging
# ============================================================
import asyncio
from pprint import pprint
from langchain_core.messages import HumanMessage


async def run_workflow():
    last_state = None
    initial_state = {
        "messages": [
            HumanMessage(
                content="Get information about ClickHouse staging and DPX tables, including PII columns and dbt logic. Table: staging_prod_db_coredb_crm_owner_account"
            )
        ]
    }

    async for step in app.astream(initial_state):
        last_state = step
        print("\n----- Step -----")
        for node_name, node_data in step.items():
            msgs = node_data.get("messages", [])
            if msgs:
                msg = msgs[-1]
                print(f"[{node_name}] {type(msg).__name__}: {msg.content}")
        print("-----------------")

    print("\n=== Final State ===")
    pprint(last_state)


if __name__ == "__main__":
    print("[DPX→ClickHouse] Starting workflow...")
    asyncio.run(run_workflow())
