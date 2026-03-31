"""ChronoTrader CLI."""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv(Path(__file__).parent.parent / ".env")

from agent.config import settings
from agent.core.metrics import (
    compute_metrics,
    load_metrics,
    load_trades,
    print_metrics_summary,
    save_trade,
    update_metrics,
    write_performance,
)
from agent.core.validation_agent import run_validation
from agent.tools import init_chainlink_tools, init_erc8004_tools

console = Console()


def init_tools() -> None:
    init_chainlink_tools(rpc_url=settings.rpc_url)
    if (
        settings.identity_registry_address
        and settings.reputation_registry_address
        and settings.validation_registry_address
        and settings.agent_private_key
    ):
        init_erc8004_tools(
            rpc_url=settings.rpc_url,
            private_key=settings.agent_private_key,
            addresses={
                "identity": settings.identity_registry_address,
                "reputation": settings.reputation_registry_address,
                "validation": settings.validation_registry_address,
            },
        )


def create_agent_card() -> dict:
    return {
        "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
        "name": settings.agent_name,
        "description": settings.agent_description,
        "image": "",
        "services": [{"name": "A2A", "endpoint": "", "version": "0.3.0"}],
        "x402Support": False,
        "active": True,
        "supportedTrust": ["reputation", "crypto-economic"],
        "capabilities": {
            "strategies": ["momentum", "mean_reversion", "yield_optimization"],
            "riskLimits": {
                "maxPositionSizePct": 20,
                "maxDailyLossPct": settings.max_daily_loss_pct,
                "maxDrawdownPct": settings.max_drawdown_pct,
            },
            "supportedAssets": ["ETH", "BTC", "USDC"],
            "supportedProtocols": ["uniswap-v3"],
        },
    }


def cmd_register() -> None:
    init_tools()
    card_path = Path("agent/data/agent_card.json")
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(create_agent_card(), indent=2))
    console.print(f"[green]Saved agent card:[/green] {card_path}")

    if settings.simulation_mode:
        console.print("[yellow]Simulation mode enabled: skipping on-chain registration.[/yellow]")
        return

    console.print("[cyan]Run `python agent/main.py status` to verify registration fields in env.[/cyan]")


def _simulate_signal(strategy: str) -> dict:
    side = "BUY" if random.random() > 0.35 else "SELL"
    position_pct = round(random.uniform(3.0, 20.0), 2)
    confidence = random.randint(5, 9)
    return {
        "strategy": strategy,
        "asset_pair": "ETH/USDC",
        "action": side,
        "position_size_pct": position_pct,
        "confidence": confidence,
        "risk_reward_ratio": round(random.uniform(2.0, 4.0), 2),
    }


def _risk_check(signal: dict) -> tuple[bool, str]:
    if signal["position_size_pct"] > 20:
        return False, "Position size exceeds 20%"
    if signal["risk_reward_ratio"] < 2:
        return False, "Risk/reward below 2"
    return True, "APPROVED"


def cmd_trade() -> None:
    init_tools()
    strategy = settings.default_strategy
    signal = _simulate_signal(strategy)
    approved, reason = _risk_check(signal)

    amount_usd = round(settings.max_position_size_usd * signal["position_size_pct"] / 100, 4)
    pnl_pct = round(random.uniform(-1.2, 1.8), 4) if approved else 0.0
    pnl_usd = round(amount_usd * pnl_pct / 100, 4)

    now = datetime.now(timezone.utc)
    tx_hash = f"0x{hashlib.sha256(f'{now.timestamp()}-{strategy}-{amount_usd}'.encode()).hexdigest()}"
    record = {
        "timestamp": now.isoformat(),
        "strategy": strategy,
        "asset_pair": signal["asset_pair"],
        "action": signal["action"],
        "amount_in_usd": amount_usd,
        "position_size_pct": signal["position_size_pct"],
        "risk_reward_ratio": signal["risk_reward_ratio"],
        "status": "EXECUTED" if approved else "REJECTED",
        "reason": reason,
        "tx_hash": tx_hash if approved else "",
        "return_pct": pnl_pct,
        "pnl_usd": pnl_usd,
        "validation_hash": f"0x{hashlib.sha256((tx_hash + reason).encode()).hexdigest()}",
    }
    save_trade(record)

    metrics = compute_metrics(load_trades())
    write_performance(metrics)

    table = Table(title="Trading Cycle")
    table.add_column("Field")
    table.add_column("Value")
    for k in ["strategy", "action", "position_size_pct", "status", "tx_hash", "pnl_usd"]:
        table.add_row(k, str(record.get(k, "")))
    console.print(table)


def cmd_loop() -> None:
    console.print(f"[cyan]Starting loop. Interval={settings.loop_interval_seconds}s[/cyan]")
    cycle = 0
    while True:
        cycle += 1
        console.print(f"[bold]Cycle {cycle}[/bold]")
        cmd_trade()
        time.sleep(settings.loop_interval_seconds)


def cmd_status() -> None:
    trades = load_trades()
    metrics = compute_metrics(trades)
    table = Table(title="ChronoTrader Status")
    table.add_column("Metric")
    table.add_column("Value")
    for k, v in metrics.items():
        table.add_row(k, str(v))
    table.add_row("network", settings.network)
    table.add_row("simulation_mode", str(settings.simulation_mode))
    table.add_row("agent_id", str(settings.agent_id))
    console.print(table)


def main() -> None:
    console.print(Panel("[bold white on dark_green] CHRONOTRADER [/bold white on dark_green]"))
    if len(sys.argv) < 2:
        console.print("Commands: register | trade | loop | validate | status")
        raise SystemExit(1)

    command = sys.argv[1].lower()
    if command == "register":
        cmd_register()
    elif command == "trade":
        cmd_trade()
    elif command == "loop":
        cmd_loop()
    elif command == "validate":
        run_validation()
    elif command == "status":
        cmd_status()
    else:
        console.print(f"Unknown command: {command}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
