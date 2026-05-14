-- Databricks Delta Lake SQL Examples
-- Purpose: demonstrate Delta Lake table management, MERGE patterns, ODS loading, retention logic, and performance optimization.

-- ---------------------------------------------------------------------
-- 1. Bronze Delta table definition
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bronze.customers_raw (
    customer_id STRING,
    full_name STRING,
    email STRING,
    status STRING,
    created_date DATE,
    _bronze_ingested_at_utc TIMESTAMP,
    _bronze_batch_id STRING,
    _source_file STRING,
    _record_hash STRING
)
USING DELTA
PARTITIONED BY (_bronze_batch_id);

-- ---------------------------------------------------------------------
-- 2. Silver Delta table definition
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS silver.customers_clean (
    customer_id STRING NOT NULL,
    full_name STRING,
    email STRING,
    status STRING,
    created_date DATE,
    _silver_processed_at_utc TIMESTAMP
)
USING DELTA;

-- ---------------------------------------------------------------------
-- 3. Gold / ODS Delta table definition
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gold.ods_customer_profile (
    customer_id STRING NOT NULL,
    full_name STRING,
    email STRING,
    status STRING,
    created_date DATE,
    transaction_count BIGINT,
    total_transaction_amount DECIMAL(18,2),
    latest_transaction_date DATE,
    document_count BIGINT,
    highest_document_classification STRING,
    ods_record_status STRING,
    _gold_built_at_utc TIMESTAMP
)
USING DELTA;

-- ---------------------------------------------------------------------
-- 4. Delta MERGE pattern: upsert clean customer records into ODS
-- ---------------------------------------------------------------------

MERGE INTO gold.ods_customer_profile AS target
USING silver.customer_profile_updates AS source
ON target.customer_id = source.customer_id

WHEN MATCHED AND target._record_hash <> source._record_hash THEN
  UPDATE SET
    target.full_name = source.full_name,
    target.email = source.email,
    target.status = source.status,
    target.transaction_count = source.transaction_count,
    target.total_transaction_amount = source.total_transaction_amount,
    target.latest_transaction_date = source.latest_transaction_date,
    target.document_count = source.document_count,
    target.highest_document_classification = source.highest_document_classification,
    target.ods_record_status = 'current',
    target._gold_built_at_utc = current_timestamp()

WHEN NOT MATCHED THEN
  INSERT (
    customer_id,
    full_name,
    email,
    status,
    created_date,
    transaction_count,
    total_transaction_amount,
    latest_transaction_date,
    document_count,
    highest_document_classification,
    ods_record_status,
    _gold_built_at_utc
  )
  VALUES (
    source.customer_id,
    source.full_name,
    source.email,
    source.status,
    source.created_date,
    source.transaction_count,
    source.total_transaction_amount,
    source.latest_transaction_date,
    source.document_count,
    source.highest_document_classification,
    'current',
    current_timestamp()
  );

-- ---------------------------------------------------------------------
-- 5. Retention / archiving pattern
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS archive.transactions_archive
USING DELTA
AS
SELECT *
FROM silver.transactions_clean
WHERE transaction_date < add_months(current_date(), -36)
   OR payment_status = 'archivable';

-- ---------------------------------------------------------------------
-- 6. Retrieval pattern for archived records
-- ---------------------------------------------------------------------

SELECT
    transaction_id,
    customer_id,
    transaction_date,
    amount,
    payment_status
FROM archive.transactions_archive
WHERE customer_id = 'C003'
ORDER BY transaction_date DESC;

-- ---------------------------------------------------------------------
-- 7. Schema evolution option for controlled loads
-- ---------------------------------------------------------------------

SET spark.databricks.delta.schema.autoMerge.enabled = true;

MERGE INTO silver.documents_clean AS target
USING bronze.documents_raw AS source
ON target.document_id = source.document_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- ---------------------------------------------------------------------
-- 8. Delta optimization examples
-- ---------------------------------------------------------------------

OPTIMIZE gold.ods_customer_profile
ZORDER BY (customer_id);

OPTIMIZE gold.ods_document_index
ZORDER BY (document_id, classification);

VACUUM archive.transactions_archive RETAIN 168 HOURS;
