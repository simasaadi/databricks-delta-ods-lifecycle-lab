from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
ARCHIVE_DIR = DATA_DIR / "archive"
GOVERNANCE_DIR = PROJECT_ROOT / "governance"

def ensure_directories():
    for path in [RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, ARCHIVE_DIR, GOVERNANCE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

def current_batch_id(prefix: str = "BATCH") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"
