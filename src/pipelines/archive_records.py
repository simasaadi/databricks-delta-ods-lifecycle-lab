from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.config import BRONZE_DIR, ARCHIVE_DIR, GOVERNANCE_DIR, ensure_directories


def load_latest_bronze_table(table_name: str) -> pd.DataFrame:
    table_path = BRONZE_DIR / table_name
    parquet_files = sorted(table_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not parquet_files:
        raise FileNotFoundError(f"No bronze parquet files found for table: {table_name}")

    return pd.read_parquet(parquet_files[0])


def classify_archive_candidates(transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = transactions.copy()

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["payment_status"] = df["payment_status"].astype(str).str.lower().str.strip()

    today = pd.Timestamp.today().normalize()
    cutoff_date = today - pd.DateOffset(years=3)

    df["archive_rule_applied"] = ""
    df.loc[df["transaction_date"] < cutoff_date, "archive_rule_applied"] = "older_than_3_years"
    df.loc[df["payment_status"] == "archivable", "archive_rule_applied"] = df["archive_rule_applied"].apply(
        lambda value: "payment_status_archivable" if value == "" else value + ";payment_status_archivable"
    )

    archive_candidates = df[df["archive_rule_applied"] != ""].copy()
    active_records = df[df["archive_rule_applied"] == ""].copy()

    archive_candidates["archive_decision"] = "archive"
    archive_candidates["archived_at_utc"] = datetime.now(timezone.utc).isoformat()
    archive_candidates["archive_storage_zone"] = "data/archive/transactions"

    active_records["archive_decision"] = "retain_active"
    active_records["archived_at_utc"] = ""
    active_records["archive_storage_zone"] = ""

    return archive_candidates, active_records


def main():
    ensure_directories()

    transactions = load_latest_bronze_table("transactions")
    archive_candidates, active_records = classify_archive_candidates(transactions)

    archive_target_dir = ARCHIVE_DIR / "transactions"
    archive_target_dir.mkdir(parents=True, exist_ok=True)

    batch_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    archive_output_path = archive_target_dir / f"transactions_archive_{batch_timestamp}.parquet"
    active_output_path = GOVERNANCE_DIR / "active_transaction_records_after_retention_review.csv"
    manifest_path = GOVERNANCE_DIR / "archive_manifest.csv"
    decision_log_path = GOVERNANCE_DIR / "retention_decision_log.csv"

    archive_candidates.to_parquet(archive_output_path, index=False)
    active_records.to_csv(active_output_path, index=False)

    manifest = pd.DataFrame(
        [
            {
                "archive_batch_id": f"ARCH-{batch_timestamp}",
                "source_table": "transactions",
                "source_layer": "bronze",
                "archive_rule": "older_than_3_years OR payment_status_archivable",
                "records_reviewed": len(transactions),
                "records_archived": len(archive_candidates),
                "records_retained_active": len(active_records),
                "archive_output_path": str(archive_output_path),
                "review_completed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )

    decision_log = pd.concat([archive_candidates, active_records], ignore_index=True, sort=False)

    manifest.to_csv(manifest_path, index=False)
    decision_log.to_csv(decision_log_path, index=False)

    print("Archive and retention review completed.")
    print(manifest.to_string(index=False))
    print()
    print(f"Archived records written to: {archive_output_path}")
    print(f"Archive manifest written to: {manifest_path}")
    print(f"Retention decision log written to: {decision_log_path}")


if __name__ == "__main__":
    main()
