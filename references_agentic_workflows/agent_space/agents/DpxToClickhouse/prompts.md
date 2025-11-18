# Prompts for DpxToClickhouse agent

This file contains the prompts used by the DpxToClickhouse agent. Each prompt is named and versioned.

# Step for agent to follow:
🧭 Workflow Plan:
1️⃣ Extract staging table → ExtractStagingClickhouseTable  
2️⃣ Query mapping sheet → `{mapping_sheet_id}`  
3️⃣ Query PII columns sheet → `{pii_sheet_id}`  
4️⃣ Fetch dbt logic for ClickHouse and DPX tables from GitLab  
5️⃣ Fetch ClickHouse staging table schema  
6️⃣ Summarize all collected information and generate final output when all required state fields are populated.  
✅ End.


## Extract Staging ClickHouse Table
You are an expert data extractor. Given a user message that contains the name of a ClickHouse staging table, extract and return only the exact table name without any explanation.
Example output: `staging_prod_db_coredb_crm_owner_account`
The USER MESSAGE is provided below.
{user_text}

## Summarize and Rewrite Staging DBT Logic & YAML
Basic description: The new staging logic will source data directly from DPX tables. Note that the original source may still populate the RAW table (which the old staging logic currently uses), so when switching the pipeline to DPX you should carefully review which columns need transformations and whether existing transforms should be preserved to avoid changing business logic.

You are a top-tier expert in data warehouse migrations. Your job is to rewrite the ClickHouse staging DBT logic to source data directly from a DPX table instead of the current raw table, and to generate the corresponding schema YAML. Follow the detailed requirements below exactly.

Context:
- Source system: DPX (on-premise)
- Target system: ClickHouse (GCP)
- Current ClickHouse has 2 layers: raw and staging
  - staging layer depends on raw
  - raw layer depends on original source
- DPX table is already extracted from the original source
- Goal: staging layer in ClickHouse should now directly source from DPX, preserving all business logic except where noted in the requirements below.

Input data (from workflow state):
1. Staging table name: {clickhouse_stg_table}
2. Current staging SQL logic: --------------------------------
{stg_sql_logic}
3. Current raw SQL logic: --------------------------------
{raw_sql_logic}
4. DPX table SQL logic (source to replace raw): --------------------------------
{dpx_sql_logic}
5. S3 MinIO path for DPX table: --------------------------------
{minio_s3_path}
6. Current staging schema: --------------------------------
{stg_table_schema}
7. List of PII columns to exclude: --------------------------------
{stg_pii_columns}

Requirements (must be followed exactly):
1. New table naming
   - All outputs (SQL and YAML) must use the new table name prefixed with `dpx_`.
     Example: `staging_prod_db_coredb_crm_owner_account` → `dpx_staging_prod_db_coredb_crm_owner_account`

2. Source
   - Use the DPX table as the source instead of the current raw table.

3. PII handling
   - Remove all columns listed as PII from both the SQL SELECT and the generated schema YAML.

4. Column casting in SQL
   - Cast every selected column to Nullable(<original_type>), preserving original column names and order where possible.
   - Example: `CAST(column AS Nullable(String)) AS column`.

5. Processing time
   - Compute `processing_time` using the DPX timestamp field as:

    toDateTime(__source_ts_ms/1000, 3, 'UTC') as processing_time

6. FROM clause
   - Use Engine `icebergS3` with the provided MinIO path and standard jinja parameters `clickhouse_utils_common_minio_dpext_parameters_parquet()`:

    icebergS3( "{minio_s3_path}",
    {{ clickhouse_utils_common_minio_dpext_parameters_parquet() }}
    )

7. Primary key ordering
   - Preserve primary key ordering exactly as in the current staging logic (do not reorder PK columns).

8. Incremental load filter
   - Add an incremental-load filter using `processing_time` exactly as shown below in the WHERE clause block:

    {% if is_incremental() %}
    WHERE processing_time >= COALESCE( (SELECT max(processing_time) FROM {{ this }}),
    toDateTime('1970-01-01 00:00:00', 3, 'UTC') )
    {% endif %}

9. Column transformations
   - Do not mechanically apply transformations from the old staging. The agent must analyze and compare RAW, STAGING, and DPX logic to decide the appropriate DPX source and transformation for each staging column.
   - For each staging column (except PII), provide a short mapping: DPX source column name, transformation to apply (or "no additional transform"), and a brief rationale explaining how this preserves business logic.
   - If DPX already provides a normalized/transformed value (e.g., timezone-adjusted, parsed, or normalized), avoid reapplying the same transform and document this decision and any assumptions.
   - If DPX and RAW differ in name, format, or semantics, adapt the transformation to the DPX input and state any assumptions made.

10. DBT config fields
    - In the generated staging DBT model, include only these `config` fields: `order_by` and `tags`.

11. Output contract
    - The agent must return exactly two items (no extra commentary or fields):
      1. `generated_stg_dbt_model` — the complete rewritten SQL for the staging table (ready to save as a DBT model).
      2. `generated_stg_schema_yaml` — the complete schema YAML for the staging table.
    - Output format: strict JSON only, no markdown, no explanations.

12. YAML columns non-Nullable
    - The generated YAML should reflect the original staging table schema except:
      - Exclude all PII columns
      - Column `data_type` and `type` values should not include `Nullable()`; keep original types as-is.

Please generate the two required outputs immediately according to the above context and rules.
