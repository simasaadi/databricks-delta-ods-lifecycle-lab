import pandas as pd

from src.utils.config import GOVERNANCE_DIR


def search_documents(query: str) -> pd.DataFrame:
    index_path = GOVERNANCE_DIR / "document_search_index.csv"

    if not index_path.exists():
        raise FileNotFoundError(
            "Document search index not found. Run python -m src.indexing.document_index_builder first."
        )

    index_df = pd.read_csv(index_path)

    query_terms = set(query.lower().split())

    matches = index_df[index_df["search_term"].isin(query_terms)].copy()

    if matches.empty:
        return pd.DataFrame(
            columns=[
                "document_id",
                "document_title",
                "document_type",
                "classification",
                "access_tier",
                "matched_terms",
                "match_score",
            ]
        )

    results = (
        matches.groupby(
            ["document_id", "document_title", "document_type", "classification", "access_tier"]
        )
        .agg(
            matched_terms=("search_term", lambda values: ", ".join(sorted(set(values)))),
            match_score=("search_term", "nunique"),
        )
        .reset_index()
        .sort_values(["match_score", "classification"], ascending=[False, True])
    )

    return results


def main():
    query = "archive support customer"
    results = search_documents(query)

    output_path = GOVERNANCE_DIR / "document_search_results_example.csv"
    results.to_csv(output_path, index=False)

    print(f"Search query: {query}")
    print(results.to_string(index=False))
    print()
    print(f"Example search results written to: {output_path}")


if __name__ == "__main__":
    main()
