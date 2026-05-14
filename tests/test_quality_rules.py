import pandas as pd

from src.quality.run_quality_checks import validate_contract


def test_quality_engine_detects_null_email():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "full_name": "Amina Patel",
                "email": None,
                "status": "active",
                "created_date": "2024-01-15",
            }
        ]
    )

    contract = {
        "table": "customers",
        "required_columns": ["customer_id", "full_name", "email", "status", "created_date"],
        "required_non_null": ["customer_id", "full_name", "email", "status"],
        "unique_columns": ["customer_id"],
        "allowed_values": {"status": ["active", "inactive"]},
        "date_columns": ["created_date"],
    }

    results = validate_contract(contract, {"customers": customers})

    failed_checks = [row for row in results if row["status"] == "FAIL"]

    assert any(row["check_type"] == "non_null" and row["column"] == "email" for row in failed_checks)


def test_quality_engine_detects_invalid_status():
    customers = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "full_name": "Amina Patel",
                "email": "amina@example.com",
                "status": "unknown",
                "created_date": "2024-01-15",
            }
        ]
    )

    contract = {
        "table": "customers",
        "required_columns": ["customer_id", "full_name", "email", "status", "created_date"],
        "required_non_null": ["customer_id", "full_name", "email", "status"],
        "unique_columns": ["customer_id"],
        "allowed_values": {"status": ["active", "inactive"]},
        "date_columns": ["created_date"],
    }

    results = validate_contract(contract, {"customers": customers})

    assert any(
        row["check_type"] == "allowed_values"
        and row["column"] == "status"
        and row["status"] == "FAIL"
        for row in results
    )
