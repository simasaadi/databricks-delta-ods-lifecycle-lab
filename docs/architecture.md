# Architecture

This project simulates a Databricks-style ODS lifecycle workflow using local Python, Parquet, YAML contracts, governance outputs, and CI/CD.

## Logical architecture

    Raw CSV source files
        |
        v
    Bronze ingestion
        - Adds ingestion timestamp
        - Adds batch ID
        - Adds source file name
        - Adds record hash
        - Writes Parquet outputs
        - Creates ingestion manifest

        |
        v
    Data contract validation
        - Required columns
        - Non-null checks
        - Unique key checks
        - Allowed value checks
        - Date validity checks
        - Positive numeric checks
        - Foreign key checks

        |
        v
    Silver transformation
        - Standardizes identifiers
        - Cleans date and numeric fields
        - Applies business validation
        - Separates clean records from rejected records
        - Creates rejected-record evidence

        |
        v
    Gold / ODS layer
        - Builds ODS customer profile
        - Builds transaction fact table
        - Builds document index table
        - Creates ODS data dictionary

        |
        v
    Lifecycle and retrieval layer
        - Applies retention rules
        - Archives eligible records
        - Creates archive manifest
        - Creates retention decision log
        - Builds searchable document index

        |
        v
    CI/CD validation
        - Runs full pipeline
        - Runs tests
        - Confirms reproducible execution

## Databricks mapping

| Local lab component | Databricks / Lakehouse equivalent |
|---|---|
| data/raw | Landing zone or external location |
| data/bronze | Bronze Delta tables |
| data/silver | Silver Delta tables |
| data/gold | Gold / ODS Delta tables |
| YAML contracts | Data contracts / expectations |
| governance outputs | Operational metadata and audit evidence |
| archive workflow | Retention and lifecycle management |
| document index | Searchable metadata layer |
| GitHub Actions | CI/CD validation |

## Why this matters

The workflow demonstrates not only pipeline construction, but also the controls around the pipeline: data quality, rejected records, metadata, retention, indexing, and repeatable validation.
