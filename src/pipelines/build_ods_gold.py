from datetime import datetime, timezone

import pandas as pd

from src.utils.config import SILVER_DIR, GOLD_DIR, GOVERNANCE_DIR, ensure_directories


CLASSIFICATION_RANK = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
}


def load_silver_table(table_name: str) -> pd.DataFrame:
    table_path = SILVER_DIR / table_name / f"{table_name}_silver.parquet"

    if not table_path.exists():
        raise FileNotFoundError(f"Silver table not found: {table_path}")

    return pd.read_parquet(table_path)


def write_gold_table(df: pd.DataFrame, table_name: str) -> str:
    target_dir = GOLD_DIR / table_name
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / f"{table_name}.parquet"
    df.to_parquet(output_path, index=False)

    return str(output_path)


def build_ods_customer_profile(customers: pd.DataFrame, transactions: pd.DataFrame, documents: pd.DataFrame) -> pd.DataFrame:
    transaction_summary = (
        transactions.groupby("customer_id")
        .agg(
            transaction_count=("transaction_id", "count"),
            total_transaction_amount=("amount", "sum"),
            latest_transaction_date=("transaction_date", "max"),
        )
        .reset_index()
    )

    document_summary = (
        documents.groupby("customer_id")
        .agg(
            document_count=("document_id", "count"),
            highest_document_classification=("classification", lambda values: max(values, key=lambda x: CLASSIFICATION_RANK.get(x, 0))),
        )
        .reset_index()
    )

    profile = customers.merge(transaction_summary, on="customer_id", how="left")
    profile = profile.merge(document_summary, on="customer_id", how="left")

    profile["transaction_count"] = profile["transaction_count"].fillna(0).astype(int)
    profile["total_transaction_amount"] = profile["total_transaction_amount"].fillna(0)
    profile["document_count"] = profile["document_count"].fillna(0).astype(int)
    profile["highest_document_classification"] = profile["highest_document_classification"].fillna("none")

    profile["ods_record_status"] = "current"
    profile["_gold_built_at_utc"] = datetime.now(timezone.utc).isoformat()

    selected_columns = [
        "customer_id",
        "full_name",
        "email",
        "status",
        "created_date",
        "transaction_count",
        "total_transaction_amount",
        "latest_transaction_date",
        "document_count",
        "highest_document_classification",
        "ods_record_status",
        "_gold_built_at_utc",
    ]

    return profile[selected_columns]


def build_ods_transaction_fact(transactions: pd.DataFrame) -> pd.DataFrame:
    fact = transactions.copy()

    fact["transaction_year"] = fact["transaction_date"].dt.year
    fact["transaction_month"] = fact["transaction_date"].dt.month
    fact["amount_band"] = pd.cut(
        fact["amount"],
        bins=[0, 250, 750, 1500, float("inf")],
        labels=["low", "medium", "high", "very_high"],
        right=True,
    ).astype(str)

    fact["ods_record_status"] = "current"
    fact["_gold_built_at_utc"] = datetime.now(timezone.utc).isoformat()

    selected_columns = [
        "transaction_id",
        "customer_id",
        "transaction_date",
        "transaction_year",
        "transaction_month",
        "amount",
        "amount_band",
        "payment_status",
        "ods_record_status",
        "_gold_built_at_utc",
    ]

    return fact[selected_columns]


def build_ods_document_index(documents: pd.DataFrame) -> pd.DataFrame:
    index = documents.copy()

    index["search_text"] = (
        index["document_title"].fillna("") + " "
        + index["document_type"].fillna("") + " "
        + index["classification"].fillna("") + " "
        + index["keywords"].fillna("")
    ).str.lower()

    index["keyword_count"] = index["keywords"].fillna("").apply(lambda value: len(str(value).split()))
    index["access_tier"] = index["classification"].map(
        {
            "public": "open",
            "internal": "staff_only",
            "confidential": "approved_users_only",
            "restricted": "exception_approval_required",
        }
    )

    index["index_status"] = "indexed"
    index["_gold_built_at_utc"] = datetime.now(timezone.utc).isoformat()

    selected_columns = [
        "document_id",
        "customer_id",
        "document_title",
        "document_type",
        "created_date",
        "classification",
        "access_tier",
        "keywords",
        "keyword_count",
        "search_text",
        "index_status",
        "_gold_built_at_utc",
    ]

    return index[selected_columns]


def build_ods_data_dictionary(outputs: list[dict]) -> pd.DataFrame:
    dictionary_rows = []

    for output in outputs:
        table_name = output["table_name"]
        df = output["dataframe"]

        for column in df.columns:
            dictionary_rows.append(
                {
                    "table_name": table_name,
                    "column_name": column,
                    "data_type": str(df[column].dtype),
                    "business_description": "To be confirmed with data owner",
                    "governance_note": "Generated as part of ODS gold-layer build",
                }
            )

    return pd.DataFrame(dictionary_rows)


def main():
    ensure_directories()

    customers = load_silver_table("customers")
    transactions = load_silver_table("transactions")
    documents = load_silver_table("documents")

    customer_profile = build_ods_customer_profile(customers, transactions, documents)
    transaction_fact = build_ods_transaction_fact(transactions)
    document_index = build_ods_document_index(documents)

    outputs = [
        {
            "table_name": "ods_customer_profile",
            "dataframe": customer_profile,
            "output_path": write_gold_table(customer_profile, "ods_customer_profile"),
        },
        {
            "table_name": "ods_transaction_fact",
            "dataframe": transaction_fact,
            "output_path": write_gold_table(transaction_fact, "ods_transaction_fact"),
        },
        {
            "table_name": "ods_document_index",
            "dataframe": document_index,
            "output_path": write_gold_table(document_index, "ods_document_index"),
        },
    ]

    summary = pd.DataFrame(
        [
            {
                "table_name": output["table_name"],
                "record_count": len(output["dataframe"]),
                "column_count": len(output["dataframe"].columns),
                "output_path": output["output_path"],
                "built_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            for output in outputs
        ]
    )

    data_dictionary = build_ods_data_dictionary(outputs)

    summary_path = GOVERNANCE_DIR / "ods_build_summary.csv"
    dictionary_path = GOVERNANCE_DIR / "ods_data_dictionary.csv"

    summary.to_csv(summary_path, index=False)
    data_dictionary.to_csv(dictionary_path, index=False)

    print("Gold ODS build completed.")
    print(summary.to_string(index=False))
    print()
    print(f"ODS build summary written to: {summary_path}")
    print(f"ODS data dictionary written to: {dictionary_path}")


if __name__ == "__main__":
    main()
