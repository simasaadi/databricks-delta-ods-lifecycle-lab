import pandas as pd

from src.pipelines.archive_records import classify_archive_candidates


def test_archive_logic_identifies_old_records():
    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "T1001",
                "customer_id": "C001",
                "transaction_date": "2020-01-01",
                "amount": 100.0,
                "payment_status": "completed",
            },
            {
                "transaction_id": "T1002",
                "customer_id": "C002",
                "transaction_date": "2025-01-01",
                "amount": 200.0,
                "payment_status": "completed",
            },
        ]
    )

    archive_candidates, active_records = classify_archive_candidates(transactions)

    assert len(archive_candidates) == 1
    assert archive_candidates.iloc[0]["transaction_id"] == "T1001"
    assert len(active_records) == 1


def test_archive_logic_identifies_archivable_status():
    transactions = pd.DataFrame(
        [
            {
                "transaction_id": "T1003",
                "customer_id": "C003",
                "transaction_date": "2025-01-01",
                "amount": 300.0,
                "payment_status": "archivable",
            }
        ]
    )

    archive_candidates, active_records = classify_archive_candidates(transactions)

    assert len(archive_candidates) == 1
    assert "payment_status_archivable" in archive_candidates.iloc[0]["archive_rule_applied"]
    assert len(active_records) == 0
