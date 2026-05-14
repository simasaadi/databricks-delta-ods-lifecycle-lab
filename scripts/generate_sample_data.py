import pandas as pd
from pathlib import Path

raw_path = Path('data/raw')
raw_path.mkdir(parents=True, exist_ok=True)

customers = pd.DataFrame([
    {"customer_id": "C001", "full_name": "Amina Patel", "email": "amina.patel@example.com", "status": "active", "created_date": "2024-01-15"},
    {"customer_id": "C002", "full_name": "Daniel Chen", "email": "daniel.chen@example.com", "status": "active", "created_date": "2024-02-20"},
    {"customer_id": "C003", "full_name": "Maya Singh", "email": None, "status": "inactive", "created_date": "2023-11-05"},
    {"customer_id": "C004", "full_name": "Omar Wilson", "email": "omar.wilson@example.com", "status": "active", "created_date": "2024-03-10"},
])

transactions = pd.DataFrame([
    {"transaction_id": "T1001", "customer_id": "C001", "transaction_date": "2025-01-10", "amount": 245.75, "payment_status": "completed"},
    {"transaction_id": "T1002", "customer_id": "C002", "transaction_date": "2025-01-12", "amount": 980.00, "payment_status": "completed"},
    {"transaction_id": "T1003", "customer_id": "C003", "transaction_date": "2021-06-18", "amount": 120.50, "payment_status": "archivable"},
    {"transaction_id": "T1004", "customer_id": "C999", "transaction_date": "2025-02-01", "amount": -45.00, "payment_status": "error"},
])

documents = pd.DataFrame([
    {"document_id": "D001", "customer_id": "C001", "document_title": "Service Agreement", "document_type": "contract", "created_date": "2024-01-20", "classification": "confidential", "keywords": "agreement service contract"},
    {"document_id": "D002", "customer_id": "C002", "document_title": "Invoice January", "document_type": "invoice", "created_date": "2025-01-15", "classification": "internal", "keywords": "invoice payment billing"},
    {"document_id": "D003", "customer_id": "C003", "document_title": "Archived Support Record", "document_type": "support_record", "created_date": "2020-04-08", "classification": "restricted", "keywords": "support archive customer issue"},
])

customers.to_csv(raw_path / 'customers.csv', index=False)
transactions.to_csv(raw_path / 'transactions.csv', index=False)
documents.to_csv(raw_path / 'documents.csv', index=False)

print('Sample raw datasets created in data/raw/')
