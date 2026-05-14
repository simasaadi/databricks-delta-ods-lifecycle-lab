from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.config import BRONZE_DIR, SILVER_DIR, GOVERNANCE_DIR, ensure_directories


def load_latest_bronze_table(table_name: str) -> pd.DataFrame:
    table_path = BRONZE_DIR / table_name
    parquet_files = sorted(table_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not parquet_files:
        raise FileNotFoundError(f"No bronze parquet files found for table: {table_name}")

    return pd.read_parquet(parquet_files[0])


def write_silver_table(df: pd.DataFrame, table_name: str) -> str:
    target_dir = SILVER_DIR / table_name
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / f"{table_name}_silver.parquet"
    df.to_parquet(output_path, index=False)

    return str(output_path)


def clean_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()

    df["customer_id"] = df["customer_id"].astype(str).str.strip().str.upper()
    df["full_name"] = df["full_name"].astype(str).str.strip()
    df["email"] = df["email"].astype("string").str.strip().str.lower()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")

    df["_silver_processed_at_utc"] = datetime.now(timezone.utc).isoformat()

    rejection_reasons = []

    for _, row in df.iterrows():
        reasons = []
        if pd.isna(row["customer_id"]) or row["customer_id"] == "":
            reasons.append("missing_customer_id")
        if pd.isna(row["full_name"]) or row["full_name"] == "":
            reasons.append("missing_full_name")
        if pd.isna(row["email"]) or row["email"] == "":
            reasons.append("missing_email")
        if row["status"] not in ["active", "inactive"]:
            reasons.append("invalid_status")
        if pd.isna(row["created_date"]):
            reasons.append("invalid_created_date")

        rejection_reasons.append(";".join(reasons))

    df["_rejection_reason"] = rejection_reasons
    rejected = df[df["_rejection_reason"] != ""].copy()
    clean = df[df["_rejection_reason"] == ""].drop(columns=["_rejection_reason"]).copy()

    return clean, rejected


def clean_transactions(df: pd.DataFrame, valid_customer_ids: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()

    df["transaction_id"] = df["transaction_id"].astype(str).str.strip().str.upper()
    df["customer_id"] = df["customer_id"].astype(str).str.strip().str.upper()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["payment_status"] = df["payment_status"].astype(str).str.strip().str.lower()

    df["_silver_processed_at_utc"] = datetime.now(timezone.utc).isoformat()

    rejection_reasons = []

    for _, row in df.iterrows():
        reasons = []
        if pd.isna(row["transaction_id"]) or row["transaction_id"] == "":
            reasons.append("missing_transaction_id")
        if row["customer_id"] not in valid_customer_ids:
            reasons.append("invalid_customer_reference")
        if pd.isna(row["transaction_date"]):
            reasons.append("invalid_transaction_date")
        if pd.isna(row["amount"]) or row["amount"] <= 0:
            reasons.append("invalid_amount")
        if row["payment_status"] not in ["completed", "pending", "archivable", "error"]:
            reasons.append("invalid_payment_status")

        rejection_reasons.append(";".join(reasons))

    df["_rejection_reason"] = rejection_reasons
    rejected = df[df["_rejection_reason"] != ""].copy()
    clean = df[df["_rejection_reason"] == ""].drop(columns=["_rejection_reason"]).copy()

    return clean, rejected


def clean_documents(df: pd.DataFrame, valid_customer_ids: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()

    df["document_id"] = df["document_id"].astype(str).str.strip().str.upper()
    df["customer_id"] = df["customer_id"].astype(str).str.strip().str.upper()
    df["document_title"] = df["document_title"].astype(str).str.strip()
    df["document_type"] = df["document_type"].astype(str).str.strip().str.lower()
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["classification"] = df["classification"].astype(str).str.strip().str.lower()
    df["keywords"] = df["keywords"].astype("string").str.strip().str.lower()

    df["_silver_processed_at_utc"] = datetime.now(timezone.utc).isoformat()

    rejection_reasons = []

    for _, row in df.iterrows():
        reasons = []
        if pd.isna(row["document_id"]) or row["document_id"] == "":
            reasons.append("missing_document_id")
        if row["customer_id"] not in valid_customer_ids:
            reasons.append("invalid_customer_reference")
        if pd.isna(row["document_title"]) or row["document_title"] == "":
            reasons.append("missing_document_title")
        if row["document_type"] not in ["contract", "invoice", "support_record"]:
            reasons.append("invalid_document_type")
        if row["classification"] not in ["public", "internal", "confidential", "restricted"]:
            reasons.append("invalid_classification")
        if pd.isna(row["created_date"]):
            reasons.append("invalid_created_date")

        rejection_reasons.append(";".join(reasons))

    df["_rejection_reason"] = rejection_reasons
    rejected = df[df["_rejection_reason"] != ""].copy()
    clean = df[df["_rejection_reason"] == ""].drop(columns=["_rejection_reason"]).copy()

    return clean, rejected


def main():
    ensure_directories()

    customers_bronze = load_latest_bronze_table("customers")
    transactions_bronze = load_latest_bronze_table("transactions")
    documents_bronze = load_latest_bronze_table("documents")

    customers_silver, customers_rejected = clean_customers(customers_bronze)
    valid_customer_ids = set(customers_silver["customer_id"])

    transactions_silver, transactions_rejected = clean_transactions(transactions_bronze, valid_customer_ids)
    documents_silver, documents_rejected = clean_documents(documents_bronze, valid_customer_ids)

    outputs = [
        {
            "table": "customers",
            "clean_records": len(customers_silver),
            "rejected_records": len(customers_rejected),
            "output_path": write_silver_table(customers_silver, "customers"),
        },
        {
            "table": "transactions",
            "clean_records": len(transactions_silver),
            "rejected_records": len(transactions_rejected),
            "output_path": write_silver_table(transactions_silver, "transactions"),
        },
        {
            "table": "documents",
            "clean_records": len(documents_silver),
            "rejected_records": len(documents_rejected),
            "output_path": write_silver_table(documents_silver, "documents"),
        },
    ]

    rejected_records = pd.concat(
        [
            customers_rejected.assign(source_table="customers"),
            transactions_rejected.assign(source_table="transactions"),
            documents_rejected.assign(source_table="documents"),
        ],
        ignore_index=True,
        sort=False,
    )

    summary_df = pd.DataFrame(outputs)

    summary_path = GOVERNANCE_DIR / "silver_transformation_summary.csv"
    rejected_path = GOVERNANCE_DIR / "rejected_records.csv"

    summary_df.to_csv(summary_path, index=False)
    rejected_records.to_csv(rejected_path, index=False)

    print("Silver transformation completed.")
    print(summary_df.to_string(index=False))
    print()
    print(f"Rejected records written to: {rejected_path}")


if __name__ == "__main__":
    main()
