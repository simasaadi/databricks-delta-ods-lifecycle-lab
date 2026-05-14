-- Data Retention Rules for ODS / Delta Lake-Style Transaction Records

-- Rule 1:
-- Archive transactions older than 3 years.

SELECT *
FROM ods_transaction_fact
WHERE transaction_date < CURRENT_DATE - INTERVAL '3 years';

-- Rule 2:
-- Archive transactions explicitly marked as archivable.

SELECT *
FROM ods_transaction_fact
WHERE payment_status = 'archivable';

-- Rule 3:
-- Keep current operational records active.

SELECT *
FROM ods_transaction_fact
WHERE transaction_date >= CURRENT_DATE - INTERVAL '3 years'
  AND payment_status <> 'archivable';
