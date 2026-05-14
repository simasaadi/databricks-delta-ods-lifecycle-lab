from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src.utils.config import BRONZE_DIR, GOVERNANCE_DIR, ensure_directories


def load_latest_bronze_table(table_name: str) -> pd.DataFrame:
    table_path = BRONZE_DIR / table_name
    parquet_files = sorted(table_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not parquet_files:
        raise FileNotFoundError(f"No bronze parquet files found for table: {table_name}")

    return pd.read_parquet(parquet_files[0])


def load_contract(contract_path: Path) -> dict:
    with open(contract_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def result(table, check_type, column, status, failed_records, message):
    return {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "table": table,
        "check_type": check_type,
        "column": column,
        "status": status,
        "failed_records": int(failed_records),
        "message": message,
    }


def validate_contract(contract: dict, tables: dict) -> list:
    table_name = contract["table"]
    df = tables[table_name]
    results = []

    required_columns = contract.get("required_columns", [])
    for column in required_columns:
        if column not in df.columns:
            results.append(result(table_name, "required_column", column, "FAIL", len(df), "Required column is missing."))
        else:
            results.append(result(table_name, "required_column", column, "PASS", 0, "Required column exists."))

    for column in contract.get("required_non_null", []):
        if column in df.columns:
            failed = df[column].isna().sum()
            status = "PASS" if failed == 0 else "FAIL"
            results.append(result(table_name, "non_null", column, status, failed, f"{failed} null values found."))

    for column in contract.get("unique_columns", []):
        if column in df.columns:
            failed = df[column].duplicated().sum()
            status = "PASS" if failed == 0 else "FAIL"
            results.append(result(table_name, "unique", column, status, failed, f"{failed} duplicate values found."))

    for column, allowed_values in contract.get("allowed_values", {}).items():
        if column in df.columns:
            invalid_mask = ~df[column].dropna().isin(allowed_values)
            failed = invalid_mask.sum()
            status = "PASS" if failed == 0 else "FAIL"
            results.append(result(table_name, "allowed_values", column, status, failed, f"{failed} invalid values found."))

    for column in contract.get("date_columns", []):
        if column in df.columns:
            parsed_dates = pd.to_datetime(df[column], errors="coerce")
            failed = parsed_dates.isna().sum()
            status = "PASS" if failed == 0 else "FAIL"
            results.append(result(table_name, "valid_date", column, status, failed, f"{failed} invalid dates found."))

    for column in contract.get("numeric_positive", []):
        if column in df.columns:
            numeric_values = pd.to_numeric(df[column], errors="coerce")
            failed = ((numeric_values <= 0) | numeric_values.isna()).sum()
            status = "PASS" if failed == 0 else "FAIL"
            results.append(result(table_name, "positive_numeric", column, status, failed, f"{failed} non-positive or invalid numeric values found."))

    for fk in contract.get("foreign_keys", []):
        column = fk["column"]
        reference_table = fk["reference_table"]
        reference_column = fk["reference_column"]

        if column in df.columns and reference_table in tables:
            reference_values = set(tables[reference_table][reference_column].dropna())
            failed = (~df[column].dropna().isin(reference_values)).sum()
            status = "PASS" if failed == 0 else "FAIL"
            message = f"{failed} records do not match {reference_table}.{reference_column}."
            results.append(result(table_name, "foreign_key", column, status, failed, message))

    return results


def main():
    ensure_directories()

    contract_files = sorted(Path("src/contracts").glob("*_contract.yml"))
    contracts = [load_contract(path) for path in contract_files]

    tables = {
        contract["table"]: load_latest_bronze_table(contract["table"])
        for contract in contracts
    }

    all_results = []
    for contract in contracts:
        all_results.extend(validate_contract(contract, tables))

    results_df = pd.DataFrame(all_results)
    issues_df = results_df[results_df["status"] == "FAIL"].copy()

    GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)

    results_path = GOVERNANCE_DIR / "data_quality_results.csv"
    issues_path = GOVERNANCE_DIR / "data_quality_issues.csv"

    results_df.to_csv(results_path, index=False)
    issues_df.to_csv(issues_path, index=False)

    print("Data quality validation completed.")
    print(results_df.groupby(["table", "status"]).size().reset_index(name="check_count").to_string(index=False))
    print()
    print(f"Results written to: {results_path}")
    print(f"Issues written to: {issues_path}")


if __name__ == "__main__":
    main()
