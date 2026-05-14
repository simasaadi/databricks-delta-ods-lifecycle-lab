from pathlib import Path

import yaml


def test_customer_contract_has_primary_key():
    contract_path = Path("src/contracts/customer_contract.yml")
    contract = yaml.safe_load(contract_path.read_text())

    assert contract["table"] == "customers"
    assert contract["primary_key"] == "customer_id"
    assert "customer_id" in contract["required_columns"]
    assert "email" in contract["required_non_null"]


def test_transaction_contract_has_retention_rule():
    contract_path = Path("src/contracts/transaction_contract.yml")
    contract = yaml.safe_load(contract_path.read_text())

    assert contract["table"] == "transactions"
    assert contract["retention_rule"] == "archive_after_3_years"
    assert "amount" in contract["numeric_positive"]


def test_document_contract_supports_indexing_classification():
    contract_path = Path("src/contracts/document_contract.yml")
    contract = yaml.safe_load(contract_path.read_text())

    assert contract["table"] == "documents"
    assert "classification" in contract["allowed_values"]
    assert "restricted" in contract["allowed_values"]["classification"]
