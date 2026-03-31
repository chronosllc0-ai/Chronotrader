"""ChronoTrader CLI."""

from __future__ import annotations

import hashlib
import json
import random
import signal
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
from agent.core.metrics import compute_metrics, load_trades, save_trade, write_performance
from agent.core.validation_agent import run_validation
from agent.tools import (
    init_chainlink_tools,
    init_erc8004_tools,
    init_uniswap_tools,
    get_erc8004_client,
)

console = Console()


def init_tools() -> None:
    init_chainlink_tools(rpc_url=settings.rpc_url)
    if settings.sandbox_risk_router_address and settings.agent_private_key:
        init_uniswap_tools(
            rpc_url=settings.rpc_url,
            private_key=settings.agent_private_key,
            router_address=settings.sandbox_risk_router_address,
        )
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

    client = get_erc8004_client()
    if client is None:
        raise RuntimeError("ERC-8004 client is not initialized; check env addresses and private key.")
    agent_uri = settings.agent_card_ipfs_uri or f"file://{card_path.resolve()}"
    agent_id = client.register_agent(agent_uri)
    console.print(f"[green]Registered on-chain with agent ID: {agent_id}[/green]")


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


def _make_hash(data: str) -> str:
    return "0x" + hashlib.sha256(data.encode()).hexdigest()


def _cmd_trade_simulated() -> None:
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

    table = Table(title="Trading Cycle (simulated)")
    table.add_column("Field")
    table.add_column("Value")
    for k in ["strategy", "action", "position_size_pct", "status", "tx_hash", "pnl_usd"]:
        table.add_row(k, str(record.get(k, "")))
    console.print(table)


def cmd_trade() -> None:
    init_tools()
    if settings.simulation_mode:
        _cmd_trade_simulated()
        return

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when SIMULATION_MODE=false")

    from crewai import Crew, Process
    from agent.core.strategy_agent import create_strategy_agent, create_market_analysis_task
    from agent.core.risk_agent import create_risk_agent, create_risk_check_task
    from agent.core.execution_agent import create_execution_agent, create_execution_task

    api_key = settings.openai_api_key
    strategy = settings.default_strategy

    strat_agent = create_strategy_agent(api_key)
    strat_task = create_market_analysis_task(
        strat_agent, f"Strategy: {strategy}. Capital: ${settings.max_position_size_usd}"
    )
    strat_result = str(
        Crew(agents=[strat_agent], tasks=[strat_task], process=Process.sequential).kickoff()
    )

    risk_agent = create_risk_agent(api_key)
    risk_task = create_risk_check_task(
        risk_agent,
        trade_signal=strat_result,
        current_capital=settings.max_position_size_usd,
        max_position_pct=20.0,
        max_daily_loss_pct=settings.max_daily_loss_pct,
        max_drawdown_pct=settings.max_drawdown_pct,
    )
    risk_result = str(
        Crew(agents=[risk_agent], tasks=[risk_task], process=Process.sequential).kickoff()
    )

    if "APPROVED" not in risk_result.upper():
        console.print("[yellow]Trade REJECTED by risk agent[/yellow]")
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy": strategy,
            "status": "REJECTED",
            "reason": risk_result[:200],
            "tx_hash": "",
            "pnl_usd": 0.0,
            "return_pct": 0.0,
            "validation_hash": _make_hash(risk_result),
        }
        save_trade(record)
        metrics = compute_metrics(load_trades())
        write_performance(metrics)
        return

    exec_agent = create_execution_agent(api_key)
    exec_task = create_execution_task(
        exec_agent, approved_trade=risk_result, agent_id=settings.agent_id
    )
    exec_result = str(
        Crew(agents=[exec_agent], tasks=[exec_task], process=Process.sequential).kickoff()
    )

    try:
        exec_data = json.loads(exec_result)
    except Exception:
        exec_data = {}

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "status": "EXECUTED" if exec_data.get("tx_hash") else "ERROR",
        "tx_hash": exec_data.get("tx_hash", ""),
        "pnl_usd": float(exec_data.get("pnl_usd", 0.0)),
        "return_pct": float(exec_data.get("return_pct", 0.0)),
        "validation_hash": exec_data.get("validation_hash") or _make_hash(exec_result),
    }
    save_trade(record)
    metrics = compute_metrics(load_trades())
    write_performance(metrics)

    table = Table(title="Trade Result")
    table.add_column("Field")
    table.add_column("Value")
    for k in ["strategy", "status", "tx_hash", "pnl_usd"]:
        table.add_row(k, str(record.get(k, "")))
    console.print(table)


def cmd_loop() -> None:
    console.print(
        f"[cyan]Starting loop. Interval={settings.loop_interval_seconds}s. Ctrl+C to stop.[/cyan]"
    )
    cycle = 0
    running = True

    def _stop(_sig, _frame):
        nonlocal running
        console.print("\n[yellow]Stopping loop gracefully...[/yellow]")
        running = False

    signal.signal(signal.SIGINT, _stop)

    while running:
        cycle += 1
        console.print(f"[bold]Cycle {cycle}[/bold]")
        try:
            cmd_trade()
        except Exception as e:
            console.print(f"[red]Cycle {cycle} error (non-fatal): {e}[/red]")

        for _ in range(settings.loop_interval_seconds):
            if not running:
                break
            time.sleep(1)
    console.print("[green]Loop stopped. State saved.[/green]")


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
