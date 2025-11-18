{{ 
    config(
        order_by = 'account_id',
        tags = ["ETC Account"]
    ) 
}}

select
    CAST(source AS Nullable(String)) AS source,
    CAST(status AS Nullable(String)) AS status,
    CAST(balance AS Nullable(Float64)) AS balance,
    CAST(cust_type AS Nullable(String)) AS cust_type,
    CAST(account_id AS Nullable(Int64)) AS account_id,
    CAST(timestamp_sub(HOUR, 7, parseDateTimeBestEffort(last_modify, 3, 'UTC')) AS Nullable(DateTime64(3, 'UTC'))) AS last_modify,
    CAST(lock_balance AS Nullable(Float64)) AS lock_balance,
    CAST(mig_cust_type AS Nullable(String)) AS mig_cust_type,
    CAST(mig_object_id AS Nullable(String)) AS mig_object_id,
    CAST(mig_wallet_id AS Nullable(String)) AS mig_wallet_id,
    CAST(account_number AS Nullable(String)) AS account_number,
    CAST(mig_object_type AS Nullable(String)) AS mig_object_type,
    CAST(available_balance AS Nullable(Float64)) AS available_balance,
    CAST(mig_object_status AS Nullable(String)) AS mig_object_status,
    CAST(parent_account_id AS Nullable(Int64)) AS parent_account_id,
    CAST(subscription_balance AS Nullable(Float64)) AS subscription_balance,
    toDateTime(__source_ts_ms/1000, 3, 'UTC') as processing_time
from icebergS3( "https://s3-dpex.vetc.com.vn/data-warehouse/dwh/019974e4-2d6d-7c81-9bbb-2ce358a8cab5/crm_owner_account-00779e2737fc4337bf7c1e31c7ed2bb6",
    {{ clickhouse_utils_common_minio_dpext_parameters_parquet() }}
)
{% if is_incremental() %}
WHERE processing_time >= COALESCE( (SELECT max(processing_time) FROM {{ this }}),
toDateTime('1970-01-01 00:00:00', 3, 'UTC') )
{% endif %}