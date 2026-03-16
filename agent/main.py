"""
ChronoTrader — Autonomous AI Trading Agent with ERC-8004 Trust
Main entry point for agent operations

Usage:
    python main.py register    # Register agent on ERC-8004
    python main.py trade       # Run a single trading cycle
    python main.py loop        # Run continuous trading loop
"""

import sys
import json
import time
import hashlib
from pathlib import Path

from crewai import Crew, Process
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment before imports that need it
load_dotenv(Path(__file__).parent.parent / ".env")

from agent.config import settings
from agent.core import (
    create_strategy_agent,
    create_risk_agent,
    create_execution_agent,
    create_market_analysis_task,
    create_risk_check_task,
    create_execution_task,
    create_registration_task,
)
from agent.tools import init_erc8004_tools, init_chainlink_tools, init_uniswap_tools

console = Console()


def init_tools():
    """Initialize all tool clients with config"""
    console.print("[cyan]Initializing tool clients...[/cyan]")

    if settings.identity_registry_address:
        init_erc8004_tools(
            rpc_url=settings.rpc_url,
            private_key=settings.agent_private_key,
            addresses={
                "identity": settings.identity_registry_address,
                "reputation": settings.reputation_registry_address,
                "validation": settings.validation_registry_address,
            },
        )
        console.print("  ✅ ERC-8004 registries connected")

    init_chainlink_tools(rpc_url=settings.rpc_url)
    console.print("  ✅ Chainlink price feeds connected")

    # TODO: Initialize with actual router address
    # init_uniswap_tools(
    #     rpc_url=settings.rpc_url,
    #     private_key=settings.agent_private_key,
    #     router_address=UNISWAP_ROUTER_ADDRESS,
    # )
    # console.print("  ✅ Uniswap router connected")


def create_agent_card() -> dict:
    """Generate the ERC-8004 agent registration JSON"""
    return {
        "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
        "name": settings.agent_name,
        "description": settings.agent_description,
        "image": "",  # TODO: Add agent logo IPFS URI
        "services": [
            {
                "name": "A2A",
                "endpoint": "",  # TODO: Set agent A2A endpoint
                "version": "0.3.0",
            },
            {
                "name": "web",
                "endpoint": "",  # TODO: Set dashboard URL
            },
        ],
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
            "supportedProtocols": ["uniswap-v3", "aave-v3"],
        },
    }


def cmd_register():
    """Register ChronoTrader on ERC-8004 Identity Registry"""
    console.print(
        Panel(
            "[bold green]ChronoTrader — Agent Registration[/bold green]",
            subtitle="ERC-8004 Identity Registry",
        )
    )

    init_tools()

    # Generate agent card
    agent_card = create_agent_card()
    card_json = json.dumps(agent_card, indent=2)
    console.print(f"\n[yellow]Agent Card:[/yellow]\n{card_json}\n")

    # TODO: Upload to IPFS and get URI
    # For now, save locally
    card_path = Path(__file__).parent / "data" / "agent_card.json"
    card_path.parent.mkdir(exist_ok=True)
    card_path.write_text(card_json)
    console.print(f"[cyan]Agent card saved to: {card_path}[/cyan]")

    # Create and run registration crew
    execution_agent = create_execution_agent(
        settings.openai_api_key, settings.openai_model
    )
    registration_task = create_registration_task(
        execution_agent, f"ipfs://TODO/{card_path.name}"
    )

    crew = Crew(
        agents=[execution_agent],
        tasks=[registration_task],
        process=Process.sequential,
        verbose=True,
    )

    console.print("\n[bold]Starting registration...[/bold]\n")
    result = crew.kickoff()
    console.print(f"\n[green]Registration result:[/green]\n{result}")


def cmd_trade():
    """Execute a single trading cycle: Analyze → Risk Check → Execute"""
    console.print(
        Panel(
            "[bold green]ChronoTrader — Trading Cycle[/bold green]",
            subtitle=f"Strategy: {settings.default_strategy}",
        )
    )

    init_tools()

    # Create agents
    strategy_agent = create_strategy_agent(
        settings.openai_api_key, settings.openai_model
    )
    risk_agent = create_risk_agent(
        settings.openai_api_key, settings.openai_model
    )
    execution_agent = create_execution_agent(
        settings.openai_api_key, settings.openai_model
    )

    # Phase 1: Market Analysis
    console.print("\n[bold cyan]Phase 1: Market Analysis[/bold cyan]")
    analysis_task = create_market_analysis_task(
        strategy_agent,
        market_context=f"Strategy: {settings.default_strategy}, Capital: ${settings.max_position_size_usd}",
    )

    analysis_crew = Crew(
        agents=[strategy_agent],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=True,
    )
    analysis_result = analysis_crew.kickoff()
    console.print(f"\n[green]Analysis:[/green]\n{analysis_result}\n")

    # Phase 2: Risk Check
    console.print("\n[bold yellow]Phase 2: Risk Validation[/bold yellow]")
    risk_task = create_risk_check_task(
        risk_agent,
        trade_signal=str(analysis_result),
        current_capital=settings.max_position_size_usd,
        max_position_pct=20.0,
        max_daily_loss_pct=settings.max_daily_loss_pct,
        max_drawdown_pct=settings.max_drawdown_pct,
    )

    risk_crew = Crew(
        agents=[risk_agent],
        tasks=[risk_task],
        process=Process.sequential,
        verbose=True,
    )
    risk_result = risk_crew.kickoff()
    console.print(f"\n[green]Risk Assessment:[/green]\n{risk_result}\n")

    # Phase 3: Execution (only if approved)
    if "APPROVED" in str(risk_result).upper():
        console.print("\n[bold green]Phase 3: Execution[/bold green]")
        exec_task = create_execution_task(
            execution_agent,
            approved_trade=str(risk_result),
            agent_id=1,  # TODO: Use actual agent ID from registration
        )

        exec_crew = Crew(
            agents=[execution_agent],
            tasks=[exec_task],
            process=Process.sequential,
            verbose=True,
        )
        exec_result = exec_crew.kickoff()
        console.print(f"\n[green]Execution Result:[/green]\n{exec_result}")
    else:
        console.print("\n[red]Trade REJECTED by Risk Agent — no execution.[/red]")

    # Record validation artifact
    cycle_data = {
        "analysis": str(analysis_result),
        "risk_check": str(risk_result),
        "timestamp": int(time.time()),
    }
    data_hash = hashlib.sha256(json.dumps(cycle_data).encode()).hexdigest()
    console.print(f"\n[cyan]Validation artifact hash: 0x{data_hash}[/cyan]")


def cmd_loop():
    """Run continuous trading loop"""
    console.print(
        Panel(
            "[bold green]ChronoTrader — Continuous Trading Mode[/bold green]",
            subtitle="Press Ctrl+C to stop",
        )
    )

    cycle = 0
    while True:
        cycle += 1
        console.print(f"\n{'='*60}")
        console.print(f"[bold]Trading Cycle #{cycle}[/bold]")
        console.print(f"{'='*60}")

        try:
            cmd_trade()
        except Exception as e:
            console.print(f"[red]Cycle error: {e}[/red]")

        # Wait between cycles (configurable)
        wait_minutes = 15
        console.print(f"\n[dim]Next cycle in {wait_minutes} minutes...[/dim]")
        time.sleep(wait_minutes * 60)


def main():
    """CLI entry point"""
    console.print(
        Panel(
            "[bold white on dark_green] CHRONOTRADER [/bold white on dark_green]\n"
            "[dim]Autonomous AI Trading Agent with ERC-8004 Trust[/dim]",
            border_style="green",
        )
    )

    if len(sys.argv) < 2:
        console.print("\nUsage: python main.py <command>\n")
        console.print("Commands:")
        console.print("  register  — Register agent on ERC-8004")
        console.print("  trade     — Run a single trading cycle")
        console.print("  loop      — Run continuous trading loop")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "register":
        cmd_register()
    elif command == "trade":
        cmd_trade()
    elif command == "loop":
        cmd_loop()
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
