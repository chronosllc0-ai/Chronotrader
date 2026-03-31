"""Validation agent for phase 4 reputation submissions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from agent.config import settings
from agent.core.reputation_scorer import compute_reputation_score, compute_strategy_scores
from agent.tools.erc8004_registry import get_erc8004_client

console = Console()


def run_validation() -> dict:
    perf_path = Path("agent/data/performance.json")
    trades_path = Path("agent/data/trades.json")

    if not perf_path.exists():
        raise FileNotFoundError("agent/data/performance.json not found")

    metrics = json.loads(perf_path.read_text())
    score_bps = compute_reputation_score(metrics)
    strategy_scores = compute_strategy_scores(trades_path)

    tx_hash = "simulated"
    if not settings.simulation_mode:
        client = get_erc8004_client()
        if client is None:
            raise RuntimeError("ERC-8004 client is not initialized")
        tx_hash = client.submit_reputation_score(
            agent_id=settings.agent_id,
            score_bps=score_bps,
            metadata=f"session:{datetime.now(timezone.utc).isoformat()}",
        )

    output = {
        "agent_id": settings.agent_id,
        "score_bps": score_bps,
        "strategy_scores": strategy_scores,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "tx_hash": tx_hash,
    }

    out_path = Path("agent/data/reputation_submission.json")
    out_path.write_text(json.dumps(output, indent=2))

    table = Table(title="Reputation Validation")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Agent ID", str(output["agent_id"]))
    table.add_row("Score (bps)", str(output["score_bps"]))
    table.add_row("Tx Hash", output["tx_hash"])
    console.print(table)

    return output


if __name__ == "__main__":
    run_validation()
