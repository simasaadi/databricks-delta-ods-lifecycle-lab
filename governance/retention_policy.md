# Data Retention and Archiving Policy

This lab uses a simple transaction retention rule to demonstrate enterprise-style data lifecycle management.

## Retention rule

Transaction records are reviewed for archival when either condition is true:

1. The transaction date is older than 3 years.
2. The payment status is marked as archivable.

## Archive outputs

Eligible records are written to:

data/archive/transactions/

## Governance evidence

Each archive run produces:

- archive_manifest.csv
- retention_decision_log.csv
- active_transaction_records_after_retention_review.csv

These files provide traceability for what was reviewed, what was archived, what was retained, and which rule was applied.
