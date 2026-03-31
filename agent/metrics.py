import json
import math
from pathlib import Path
from datetime import datetime

METRICS_FILE = Path(__file__).parent / "data" / "performance.json"

CYCLES_PER_YEAR = 35040  # 15-minute cycles → ~35,040 per year


def load_metrics() -> dict:
    """Load existing performance metrics or return defaults."""
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
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


def update_metrics(trade_result: dict, amount_in_usd: float, amount_out_usd: float) -> dict:
    """Update metrics after a trade and recalculate Sharpe/drawdown."""
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

    drawdown = (metrics["peak_capital"] - metrics["current_capital"]) / metrics["peak_capital"] * 100
    metrics["max_drawdown_pct"] = max(metrics["max_drawdown_pct"], drawdown)

    # Calculate Sharpe ratio (annualized, sample std dev, 15-min cycles → ~35,040 cycles/year)
    returns = metrics["returns"]
    if len(returns) >= 2:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_return = math.sqrt(variance)
        if std_return > 0:
            metrics["sharpe_ratio"] = (avg_return / std_return) * math.sqrt(CYCLES_PER_YEAR)
        else:
            metrics["sharpe_ratio"] = 0.0
    else:
        metrics["sharpe_ratio"] = 0.0

    metrics["win_rate"] = metrics["winning_trades"] / metrics["total_trades"] * 100

    # Add to history
    metrics["trade_history"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "pnl_usd": pnl,
        "return_pct": return_pct,
        "tx_hash": trade_result.get("tx_hash"),
        "validation_hash": trade_result.get("validation_hash"),
    })

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2))
    return metrics


def print_metrics_summary(metrics: dict):
    """Print a rich summary of current performance."""
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
