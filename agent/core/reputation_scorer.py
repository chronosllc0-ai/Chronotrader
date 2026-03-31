"""Reputation scoring utilities for phase 4."""

from __future__ import annotations

import json
import math
from pathlib import Path


def compute_reputation_score(metrics: dict) -> int:
    sharpe = float(metrics.get("sharpe_ratio", 0.0))
    win_rate = float(metrics.get("win_rate", 0.0))
    drawdown = float(metrics.get("max_drawdown_pct", 0.0))

    sharpe_score = min(4000, int(max(0.0, sharpe / 2.0) * 4000))
    win_score = min(3500, int(max(0.0, win_rate - 50.0) / 20.0 * 3500))
    dd_score = max(0, int((1 - min(1.0, drawdown / 15.0)) * 2500))

    total = sharpe_score + win_score + dd_score
    if int(metrics.get("executed_trades", metrics.get("total_trades", 0))) > 0:
        total = max(500, total)
    return min(9999, total)


def compute_strategy_scores(trades_path: Path) -> dict:
    if not trades_path.exists():
        return {}
    trades = json.loads(trades_path.read_text())

    per_strategy: dict[str, dict] = {}
    for t in trades:
        if t.get("status") != "EXECUTED":
            continue
        strategy = t.get("strategy", "momentum")
        per_strategy.setdefault(strategy, {"returns": [], "pnl": 0.0, "wins": 0, "count": 0})
        ret = float(t.get("return_pct", 0.0))
        pnl = float(t.get("pnl_usd", 0.0))
        item = per_strategy[strategy]
        item["returns"].append(ret)
        item["pnl"] += pnl
        item["count"] += 1
        if pnl > 0:
            item["wins"] += 1

    out = {}
    for strategy, d in per_strategy.items():
        mean = sum(d["returns"]) / d["count"] if d["count"] else 0.0
        var = sum((r - mean) ** 2 for r in d["returns"]) / d["count"] if d["count"] else 0.0
        std = math.sqrt(var)
        sharpe = (mean / std) * math.sqrt(365) if std > 0 else 0.0
        out[strategy] = {
            "sharpe": round(sharpe, 4),
            "total_pnl": round(d["pnl"], 4),
            "trade_count": d["count"],
            "win_rate": round((d["wins"] / d["count"] * 100) if d["count"] else 0.0, 2),
        }
    return out
