import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.config import RAW_DIR, BRONZE_DIR, GOVERNANCE_DIR, ensure_directories, current_batch_id


def create_record_hash(row: pd.Series) -> str:
    row_payload = json.dumps(row.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(row_payload.encode("utf-8")).hexdigest()


def ingest_csv_to_bronze(source_file: Path, batch_id: str) -> dict:
    table_name = source_file.stem
    target_dir = BRONZE_DIR / table_name
    target_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(source_file)

    ingestion_time = datetime.now(timezone.utc).isoformat()
    df["_bronze_ingested_at_utc"] = ingestion_time
    df["_bronze_batch_id"] = batch_id
    df["_source_file"] = source_file.name
    df["_record_hash"] = df.apply(create_record_hash, axis=1)

    output_file = target_dir / f"{table_name}_{batch_id}.parquet"
    df.to_parquet(output_file, index=False)

    return {
        "bronze_table": table_name,
        "source_file": source_file.name,
        "records_ingested": len(df),
        "columns_after_ingestion": len(df.columns),
        "batch_id": batch_id,
        "output_path": str(output_file),
    }


def main():
    ensure_directories()

    raw_files = sorted(RAW_DIR.glob("*.csv"))

    if not raw_files:
        raise FileNotFoundError(
            "No CSV files found in data/raw. Run python scripts/generate_sample_data.py first."
        )

    batch_id = current_batch_id("BRZ")
    results = [ingest_csv_to_bronze(file, batch_id) for file in raw_files]

    manifest = pd.DataFrame(results)

    manifest_path = BRONZE_DIR / f"bronze_ingestion_manifest_{batch_id}.csv"
    governance_manifest_path = GOVERNANCE_DIR / "bronze_ingestion_manifest.csv"

    manifest.to_csv(manifest_path, index=False)
    manifest.to_csv(governance_manifest_path, index=False)

    print("Bronze ingestion completed.")
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
