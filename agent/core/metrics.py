"""Performance tracking helpers for trading sessions."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRADES_JSON = DATA_DIR / "trades.json"
TRADES_CSV = DATA_DIR / "trades.csv"
PERFORMANCE_JSON = DATA_DIR / "performance.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_trades() -> list[dict[str, Any]]:
    _ensure_data_dir()
    if not TRADES_JSON.exists():
        return []
    return json.loads(TRADES_JSON.read_text())


def save_trade(record: dict[str, Any]) -> None:
    trades = load_trades()
    trades.append(record)
    TRADES_JSON.write_text(json.dumps(trades, indent=2))

    is_new = not TRADES_CSV.exists()
    with TRADES_CSV.open("a", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=sorted(record.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(record)


def compute_metrics(trades: list[dict[str, Any]]) -> dict[str, float]:
    executed = [t for t in trades if t.get("status") == "EXECUTED"]
    if not executed:
        return {
            "total_trades": 0,
            "executed_trades": 0,
            "win_rate": 0.0,
            "total_pnl_usd": 0.0,
            "avg_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
        }

    returns = [float(t.get("return_pct", 0.0)) for t in executed]
    pnls = [float(t.get("pnl_usd", 0.0)) for t in executed]
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        dd = ((peak - equity) / peak * 100) if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    mean = sum(returns) / len(returns)
    var = sum((x - mean) ** 2 for x in returns) / len(returns)
    std = math.sqrt(var)
    sharpe = (mean / std) * math.sqrt(365) if std > 0 else 0.0

    return {
        "total_trades": len(trades),
        "executed_trades": len(executed),
        "win_rate": round((sum(1 for p in pnls if p > 0) / len(executed)) * 100, 2),
        "total_pnl_usd": round(sum(pnls), 4),
        "avg_return_pct": round(mean, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown_pct": round(max_dd, 4),
    }


def write_performance(metrics: dict[str, Any]) -> None:
    _ensure_data_dir()
    PERFORMANCE_JSON.write_text(json.dumps(metrics, indent=2))
