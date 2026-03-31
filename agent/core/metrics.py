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


# ---------------------------------------------------------------------------
# Phase 2: load_metrics / update_metrics / print_metrics_summary
# ---------------------------------------------------------------------------

CYCLES_PER_YEAR = 35040  # 15-minute cycles → ~35,040 per year


def load_metrics() -> dict[str, Any]:
    """Load existing performance metrics from performance.json or return defaults."""
    _ensure_data_dir()
    if PERFORMANCE_JSON.exists():
        return json.loads(PERFORMANCE_JSON.read_text())
    return {
        "total_trades": 0,
        "winning_trades": 0,
        "total_pnl_usd": 0.0,
        "returns": [],
        "peak_capital": 1000.0,
        "current_capital": 1000.0,
        "max_drawdown_pct": 0.0,
        "trade_history": [],
    }


def update_metrics(
    trade_result: dict[str, Any],
    amount_in_usd: float,
    amount_out_usd: float,
) -> dict[str, Any]:
    """Update metrics after a trade and recalculate Sharpe / drawdown."""
    from datetime import datetime, timezone

    metrics = load_metrics()

    pnl = amount_out_usd - amount_in_usd
    return_pct = (pnl / amount_in_usd) * 100 if amount_in_usd > 0 else 0.0

    metrics["total_trades"] += 1
    metrics["total_pnl_usd"] += pnl
    metrics["current_capital"] += pnl
    metrics["returns"].append(return_pct)

    if pnl > 0:
        metrics["winning_trades"] += 1

    # Update peak capital and drawdown
    if metrics["current_capital"] > metrics["peak_capital"]:
        metrics["peak_capital"] = metrics["current_capital"]

    drawdown = (
        (metrics["peak_capital"] - metrics["current_capital"])
        / metrics["peak_capital"]
        * 100
    )
    metrics["max_drawdown_pct"] = max(metrics["max_drawdown_pct"], drawdown)

    # Calculate Sharpe ratio (annualized, sample std dev, 15-min cycles)
    returns = metrics["returns"]
    if len(returns) >= 2:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = math.sqrt(variance)
        if std_return > 0:
            metrics["sharpe_ratio"] = (avg_return / std_return) * math.sqrt(
                CYCLES_PER_YEAR
            )
        else:
            metrics["sharpe_ratio"] = 0.0
    else:
        metrics["sharpe_ratio"] = 0.0

    metrics["win_rate"] = metrics["winning_trades"] / metrics["total_trades"] * 100

    # Add to history
    metrics["trade_history"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pnl_usd": pnl,
            "return_pct": return_pct,
            "tx_hash": trade_result.get("tx_hash"),
            "validation_hash": trade_result.get("validation_hash"),
        }
    )

    PERFORMANCE_JSON.write_text(json.dumps(metrics, indent=2))
    return metrics


def print_metrics_summary(metrics: dict[str, Any]) -> None:
    """Print a Rich summary table of current performance."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="ChronoTrader Performance", style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Total Trades", str(metrics["total_trades"]))
    table.add_row("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
    table.add_row("Total PnL", f"${metrics['total_pnl_usd']:.2f}")
    table.add_row("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.3f}")
    table.add_row("Max Drawdown", f"{metrics['max_drawdown_pct']:.2f}%")
    table.add_row("Current Capital", f"${metrics['current_capital']:.2f}")

    console.print(table)
