import re
from datetime import datetime, timezone

import pandas as pd

from src.utils.config import GOLD_DIR, GOVERNANCE_DIR, ensure_directories


def load_gold_document_index() -> pd.DataFrame:
    index_path = GOLD_DIR / "ods_document_index" / "ods_document_index.parquet"

    if not index_path.exists():
        raise FileNotFoundError(
            "Gold document index not found. Run python -m src.pipelines.build_ods_gold first."
        )

    return pd.read_parquet(index_path)


def tokenize(text: str) -> list[str]:
    if pd.isna(text):
        return []

    return sorted(set(re.findall(r"[a-zA-Z0-9]+", str(text).lower())))


def build_search_terms(index_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in index_df.iterrows():
        terms = tokenize(row.get("search_text", ""))

        for term in terms:
            rows.append(
                {
                    "document_id": row["document_id"],
                    "document_title": row["document_title"],
                    "document_type": row["document_type"],
                    "classification": row["classification"],
                    "access_tier": row["access_tier"],
                    "search_term": term,
                    "index_status": "indexed",
                    "indexed_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            )

    return pd.DataFrame(rows)


def main():
    ensure_directories()

    index_df = load_gold_document_index()
    search_terms_df = build_search_terms(index_df)

    output_path = GOVERNANCE_DIR / "document_search_index.csv"
    summary_path = GOVERNANCE_DIR / "document_index_summary.csv"

    search_terms_df.to_csv(output_path, index=False)

    summary = pd.DataFrame(
        [
            {
                "documents_indexed": index_df["document_id"].nunique(),
                "search_terms_created": len(search_terms_df),
                "restricted_or_confidential_documents": index_df[
                    index_df["classification"].isin(["restricted", "confidential"])
                ]["document_id"].nunique(),
                "index_output": str(output_path),
                "built_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )

    summary.to_csv(summary_path, index=False)

    print("Document search index created.")
    print(summary.to_string(index=False))
    print()
    print(f"Search index written to: {output_path}")


if __name__ == "__main__":
    main()
