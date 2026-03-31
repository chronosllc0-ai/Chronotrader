# agent/core/trade_logger.py

import csv
import json
from pathlib import Path
from datetime import datetime, timezone

TRADES_JSON = Path(__file__).parent.parent / "data" / "trades.json"
TRADES_CSV = Path(__file__).parent.parent / "data" / "trades.csv"

CSV_FIELDS = [
    "timestamp", "cycle", "action", "token_in", "token_out",
    "amount_in_usd", "amount_out_usd", "pnl_usd", "tx_hash",
    "validation_hash", "status", "error"
]

def log_trade(cycle: int, action: str, token_in: str, token_out: str,
              amount_in_usd: float, amount_out_usd: float,
              tx_hash: str | None, validation_hash: str | None,
              status: str, error: str | None = None) -> dict:
    """Append a trade record to both JSON and CSV logs."""
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": cycle,
        "action": action,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in_usd": amount_in_usd,
        "amount_out_usd": amount_out_usd,
        "pnl_usd": amount_out_usd - amount_in_usd,
        "tx_hash": tx_hash,
        "validation_hash": validation_hash,
        "status": status,   # "EXECUTED", "REJECTED", "SKIPPED", "ERROR"
        "error": error,
    }
    
    # JSON log — append to array
    TRADES_JSON.parent.mkdir(exist_ok=True)
    trades = []
    if TRADES_JSON.exists():
        trades = json.loads(TRADES_JSON.read_text())
    trades.append(record)
    TRADES_JSON.write_text(json.dumps(trades, indent=2))
    
    # CSV log — append row
    write_header = not TRADES_CSV.exists()
    with open(TRADES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: record.get(k, "") for k in CSV_FIELDS})
    
    return record
