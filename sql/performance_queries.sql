-- Databricks / Delta Lake Performance Tuning Examples

-- 1. Inspect table history for operational traceability.
DESCRIBE HISTORY gold.ods_customer_profile;

-- 2. Check table detail and file layout.
DESCRIBE DETAIL gold.ods_customer_profile;

-- 3. Optimize frequently queried ODS tables.
OPTIMIZE gold.ods_customer_profile
ZORDER BY (customer_id);

OPTIMIZE gold.ods_transaction_fact
ZORDER BY (customer_id, transaction_date);

-- 4. Partition review query for transaction fact.
SELECT
    transaction_year,
    transaction_month,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM gold.ods_transaction_fact
GROUP BY transaction_year, transaction_month
ORDER BY transaction_year, transaction_month;

-- 5. Identify restricted document records for access review.
SELECT
    classification,
    access_tier,
    COUNT(*) AS document_count
FROM gold.ods_document_index
GROUP BY classification, access_tier
ORDER BY document_count DESC;

-- 6. Example query that benefits from ZORDER on document_id and classification.
SELECT *
FROM gold.ods_document_index
WHERE classification IN ('confidential', 'restricted')
  AND document_id = 'D003';

-- 7. Vacuum archived records after the approved retention window.
VACUUM archive.transactions_archive RETAIN 168 HOURS;
