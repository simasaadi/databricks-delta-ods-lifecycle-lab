# Databricks Delta ODS Lifecycle Lab

[![data-engineering-ci](https://github.com/simasaadi/databricks-delta-ods-lifecycle-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/simasaadi/databricks-delta-ods-lifecycle-lab/actions/workflows/ci.yml)

A Databricks-style data engineering lab demonstrating Delta Lake table design, ODS schema modeling, PySpark/Python-style ETL patterns, data contracts, data quality validation, retention and archiving logic, document indexing, metadata tracking, and CI/CD validation.

## Why this project matters

This project simulates the kind of data lifecycle workflow used in enterprise data platforms:

    raw CSV data
      -> bronze ingestion
      -> data contract validation
      -> silver cleaned tables
      -> gold ODS tables
      -> retention and archiving review
      -> document indexing and searchable retrieval
      -> automated tests and CI

The project is designed to show practical data engineering and governance capabilities that matter in Databricks Developer, Data Engineer, Data Governance Engineer, and cloud data platform roles.

## Role alignment

This lab demonstrates hands-on capability across:

- Databricks-style lakehouse architecture
- Delta Lake-inspired bronze, silver, and gold layers
- Operational Data Store modeling
- Data contracts using YAML
- Data quality validation and rejected-record handling
- Data retention and archiving workflows
- Document indexing and metadata-based search
- Governance evidence files
- Automated testing with pytest
- CI/CD using GitHub Actions

## Repository structure

    data/
      raw/        Source CSV files
      bronze/     Ingested Parquet tables with metadata columns
      silver/     Cleaned operational tables
      gold/       ODS-style curated tables
      archive/    Archived transaction records

    src/
      pipelines/  Ingestion, transformation, ODS build, archiving
      quality/    Data quality validation engine
      contracts/  YAML data contracts
      indexing/   Document indexing and search workflow
      utils/      Shared project configuration

    governance/
      Data quality results, issue outputs, retention logs, ODS data dictionary, index summaries

    tests/
      Unit tests for contracts, data quality rules, and archiving logic

    .github/workflows/
      CI workflow that runs the full pipeline and tests

## Pipeline outputs

The pipeline generates governance-ready evidence files, including:

- governance/bronze_ingestion_manifest.csv
- governance/data_quality_results.csv
- governance/data_quality_issues.csv
- governance/silver_transformation_summary.csv
- governance/rejected_records.csv
- governance/ods_build_summary.csv
- governance/ods_data_dictionary.csv
- governance/archive_manifest.csv
- governance/retention_decision_log.csv
- governance/document_search_index.csv
- governance/document_search_results_example.csv

## How to run locally

Install dependencies:

    python -m pip install -r requirements.txt

Run the full pipeline:

    python scripts/run_all_pipeline.py

Run tests only:

    pytest

## Technical stack

- Python
- pandas
- PyArrow / Parquet
- YAML data contracts
- pytest
- GitHub Actions
- Databricks-style bronze, silver, gold architecture
- Delta Lake-inspired ODS and lifecycle patterns

## Current status

The project currently includes a working end-to-end local pipeline, governance evidence outputs, automated tests, and GitHub Actions CI.

## Future improvements

Planned enhancements include adding Spark-native transformations, Delta Lake merge examples, performance optimization examples, visual architecture diagrams, and optional Databricks notebook exports.
