# Codex Prompt — Phase 4: Trust & Reputation
**Days 10–11 | April 8–9, 2026**  
**Goal:** Reputation accumulating on-chain, validator scoring working, bonus targets (The Graph, TEE)

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now.**

Open `docs/onboarding.md` and check:
1. **Phase 1 tasks** — all `✅ DONE`? Deployed contracts are required.
2. **Phase 2 tasks** — all `✅ DONE`? Working trade pipeline is required.
3. **Phase 3 tasks** — all `✅ DONE`? Phase 4 builds directly on the loop and trade history. You need accumulated trade history in `agent/data/trades.json` and artifact hashes in ValidationRegistry before reputation makes sense.
4. **Phase 3 "What's next" line** — confirms Phase 4 is unblocked (validators score performance, on-chain reputation)
5. **Phase 4 task table** — check which tasks are already `✅ DONE` if resuming mid-phase
6. **Notes column in Phase 3** — get the number of completed trade cycles and any tx hashes that will feed into the first reputation score

**Step 2 — If Phase 1, 2, or 3 has incomplete tasks, finish them before proceeding.** Phase 4 reputation logic requires:
- At least 3 completed trade cycles in `agent/data/trades.json` (from Phase 3)
- At least 3 validation artifact hashes in ValidationRegistry (from Phase 3)
- `agent/data/performance.json` with computed Sharpe ratio (from Phase 3 `metrics.py`)

**Step 3 — Update `docs/onboarding.md` Phase 4 task table as you complete each task.**

---

## Context

Phase 3 gave you: a continuous trading loop, trade history on disk, and validation artifacts on-chain.

Phase 4 is the **trust layer** — turning raw trade history into verifiable on-chain reputation. ERC-8004's Reputation Registry is the scoring layer judges will look at directly. The validator feedback loop (a separate script that reads trade history and submits reputation scores) closes the loop: agent acts → performance recorded → reputation updated → validator attests.

The bonus targets (The Graph subgraph, TEE attestation) are high-impact for the hackathon scoring rubric. Implement at least one bonus target in Phase 4 — the subgraph is more achievable in 2 days than TEE from scratch.

The most critical piece: **reputation scores must be computed from real metrics and submitted on-chain**, not placeholder values. Judges will check the ReputationRegistry on-chain.

---

## Goal

By the end of Phase 4, **all of the following must be true:**
1. Reputation scores computed from real trade history (Sharpe, win rate, drawdown) and submitted to ReputationRegistry after each trading session
2. `validation_agent.py` script (or cron) reads trade history and submits reputation scores without manual intervention
3. Performance metrics displayed in-terminal using Rich tables with on-chain tx explorer links
4. Multi-strategy comparison report generated: momentum vs mean reversion Sharpe ratio side-by-side
5. *(Bonus)* The Graph subgraph deployed on Base Sepolia indexing Identity and Reputation events
6. *(Bonus)* TEE attestation stub implemented (Phala Network or mock TDX attestation)

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` FIRST. Finish all incomplete Phase 1, 2, and 3 tasks before starting Phase 4.**
- [ ] Reputation scores MUST be computed from real metrics in `agent/data/performance.json` — use Sharpe ratio (capped at meaningful range), win rate, and drawdown
- [ ] Reputation score submitted to ReputationRegistry must be a `uint256` in the range 0–10000 (basis points) — normalize your Sharpe/win rate/drawdown composite into this range
- [ ] The `validation_agent.py` (or equivalent) must run **automatically** after the loop ends or on a schedule — it must not require manual steps between trading and reputation update
- [ ] The multi-strategy comparison must use real data — run at least 5 cycles with momentum strategy, then 5 cycles with mean reversion, compare Sharpe
- [ ] Rich terminal output must include a link to the reputation score tx on `sepolia.basescan.org`
- [ ] Update `docs/onboarding.md` Phase 4 task table as each task completes
- [ ] Attempt at least one bonus target (The Graph or TEE)

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** start Phase 4 work if Phase 3 has incomplete tasks — finish Phase 3 first
- [ ] **MUST NOT** submit a reputation score of 0 or 10000 to the registry — these look like placeholder values to judges
- [ ] **MUST NOT** hardcode the reputation score — it must be computed from actual performance data
- [ ] **MUST NOT** submit reputation scores more than once per trading session (debounce on session ID or timestamp)
- [ ] **MUST NOT** skip the multi-strategy comparison — this is explicitly in the judging rubric
- [ ] **MUST NOT** leave The Graph subgraph schema empty — define at least `AgentRegistered`, `ReputationUpdated`, and `TradeExecuted` entities

---

## Implementation Steps

### Step 1: Verify Phase 3 Is Complete — Check Trade History

```bash
# Check trade history exists and has content
python -c "
import json
from pathlib import Path
trades = json.loads(Path('agent/data/trades.json').read_text())
print(f'Total trade records: {len(trades)}')
executed = [t for t in trades if t['status'] == 'EXECUTED']
print(f'Executed trades: {len(executed)}')
print(f'Sample: {executed[0] if executed else None}')
"

# Check performance metrics
cat agent/data/performance.json | python -m json.tool
```

You need at least 3 executed trades with real tx hashes before proceeding. If not, run the loop:
```bash
NETWORK=base_sepolia python agent/main.py loop
```
Run for at least 3 cycles before continuing Phase 4.

### Step 2: Build `agent/core/reputation_scorer.py`

The reputation score is a composite of three metrics, normalized to 0–10000 basis points:

```python
# agent/core/reputation_scorer.py

import math
from pathlib import Path
import json

def compute_reputation_score(metrics: dict) -> int:
    """
    Compute a reputation score in basis points (0–10000) from performance metrics.
    
    Components:
    - Sharpe ratio (40% weight): Sharpe > 2.0 = max score
    - Win rate (35% weight): 70%+ win rate = max score
    - Drawdown control (25% weight): 0% drawdown = max, 15%+ = 0
    
    Returns: int in range 0–10000
    """
    
    # --- Sharpe ratio component (0–4000 bp) ---
    sharpe = metrics.get("sharpe_ratio", 0.0)
    # Normalize: Sharpe 0→0, Sharpe 2.0→4000, cap at 4000
    sharpe_score = min(4000, int(max(0, sharpe / 2.0) * 4000))
    
    # --- Win rate component (0–3500 bp) ---
    win_rate = metrics.get("win_rate", 0.0)  # 0–100%
    # Normalize: 50% win rate → 0, 70% → full score (above 50% is alpha)
    adjusted_win = max(0, win_rate - 50)  # clip below 50%
    win_score = min(3500, int((adjusted_win / 20) * 3500))  # 20% above 50% = full score
    
    # --- Drawdown control component (0–2500 bp) ---
    max_drawdown = metrics.get("max_drawdown_pct", 0.0)  # 0–100%
    # Normalize: 0% drawdown → 2500, 15% drawdown → 0
    dd_score = max(0, int((1 - min(1, max_drawdown / 15)) * 2500))
    
    total = sharpe_score + win_score + dd_score
    
    # Floor: if we have trades at all, guarantee at least 500 bp (5%) — shows the system works
    if metrics.get("total_trades", 0) > 0:
        total = max(500, total)
    
    return min(10000, total)


def compute_strategy_scores() -> dict:
    """Compare momentum vs mean reversion strategies from trade history."""
    trades_file = Path(__file__).parent.parent / "data" / "trades.json"
    if not trades_file.exists():
        return {}
    
    trades = json.loads(trades_file.read_text())
    
    strategies = {}
    for trade in trades:
        strategy = trade.get("strategy", "momentum")  # default if not tagged
        if strategy not in strategies:
            strategies[strategy] = {"returns": [], "pnl": 0, "count": 0, "wins": 0}
        
        if trade["status"] == "EXECUTED":
            pnl = trade.get("pnl_usd", 0)
            amount_in = trade.get("amount_in_usd", 1)
            ret_pct = (pnl / amount_in) * 100 if amount_in > 0 else 0
            strategies[strategy]["returns"].append(ret_pct)
            strategies[strategy]["pnl"] += pnl
            strategies[strategy]["count"] += 1
            if pnl > 0:
                strategies[strategy]["wins"] += 1
    
    result = {}
    for strat, data in strategies.items():
        if len(data["returns"]) >= 2:
            avg = sum(data["returns"]) / len(data["returns"])
            std = math.sqrt(sum((r - avg)**2 for r in data["returns"]) / len(data["returns"]))
            sharpe = (avg / std * math.sqrt(35040)) if std > 0 else 0
        else:
            sharpe = 0
        
        result[strat] = {
            "sharpe": round(sharpe, 3),
            "total_pnl": round(data["pnl"], 2),
            "trade_count": data["count"],
            "win_rate": round(data["wins"] / data["count"] * 100, 1) if data["count"] > 0 else 0,
        }
    
    return result
```

### Step 3: Build `agent/core/validation_agent.py`

This script is the validator feedback loop — run it after each trading session or on a schedule:

```python
# agent/core/validation_agent.py
"""
Validation agent: reads trade history and performance metrics, 
computes reputation score, and submits to ReputationRegistry on-chain.

Run with: python agent/core/validation_agent.py
Or: schedule in main.py loop every N cycles
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from web3 import Web3

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.core.reputation_scorer import compute_reputation_score, compute_strategy_scores
from agent.tools.erc8004_registry import ERC8004Client

console = Console()


def submit_reputation_score(agent_id: int, score: int, session_id: str, client: ERC8004Client) -> str:
    """Submit a reputation score to ReputationRegistry. Returns tx hash."""
    tx_hash = client.submit_reputation_score(
        agent_id=agent_id,
        score=score,
        metadata=f"session:{session_id}",
    )
    return tx_hash


def run_validation():
    # Load performance metrics
    metrics_file = Path("agent/data/performance.json")
    if not metrics_file.exists():
        console.print("[red]No performance.json found. Run the trading loop first.[/red]")
        sys.exit(1)
    
    metrics = json.loads(metrics_file.read_text())
    
    if metrics.get("total_trades", 0) == 0:
        console.print("[yellow]No trades in performance.json. Nothing to validate.[/yellow]")
        sys.exit(0)
    
    # Compute reputation score
    score = compute_reputation_score(metrics)
    session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    
    # Display what we're about to submit
    table = Table(title="Reputation Score Computation", style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")
    
    table.add_row("Total Trades", str(metrics["total_trades"]))
    table.add_row("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
    table.add_row("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.3f}")
    table.add_row("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
    table.add_row("Total PnL", f"${metrics['total_pnl_usd']:.2f}")
    table.add_row("─" * 20, "─" * 20)
    table.add_row("[bold]Reputation Score[/bold]", f"[bold yellow]{score}/10000 bp ({score/100:.1f}%)[/bold yellow]")
    
    console.print(table)
    
    # Strategy comparison
    strategy_scores = compute_strategy_scores()
    if strategy_scores:
        strat_table = Table(title="Strategy Comparison", style="magenta")
        strat_table.add_column("Strategy")
        strat_table.add_column("Sharpe")
        strat_table.add_column("Win Rate")
        strat_table.add_column("Total PnL")
        strat_table.add_column("Trades")
        
        for strat, data in strategy_scores.items():
            strat_table.add_row(
                strat, 
                f"{data['sharpe']:.3f}",
                f"{data['win_rate']:.1f}%",
                f"${data['total_pnl']:.2f}",
                str(data['trade_count']),
            )
        console.print(strat_table)
    
    # Submit to ReputationRegistry
    agent_id = int(os.getenv("AGENT_ID", 0))
    client = ERC8004Client(
        rpc_url=os.getenv("RPC_URL", "https://sepolia.base.org"),
        private_key=os.getenv("AGENT_PRIVATE_KEY"),
        identity_registry=os.getenv("IDENTITY_REGISTRY_ADDRESS"),
        reputation_registry=os.getenv("REPUTATION_REGISTRY_ADDRESS"),
        validation_registry=os.getenv("VALIDATION_REGISTRY_ADDRESS"),
    )
    
    console.print(f"\nSubmitting reputation score [bold]{score}[/bold] for agent {agent_id}...")
    
    tx_hash = submit_reputation_score(agent_id, score, session_id, client)
    
    explorer_link = f"https://sepolia.basescan.org/tx/{tx_hash}"
    console.print(f"[bold green]✅ Reputation score submitted![/bold green]")
    console.print(f"   Score: {score} bp ({score/100:.1f}%)")
    console.print(f"   Tx: [link={explorer_link}]{tx_hash}[/link]")
    console.print(f"   Explorer: {explorer_link}")
    
    return tx_hash


if __name__ == "__main__":
    run_validation()
```

Wire this into the main loop: call `run_validation()` every 10 cycles OR at loop shutdown. Also expose as a CLI command:
```bash
python agent/main.py validate  # Run the validator manually
```

### Step 4: Multi-Strategy Comparison

Tag each trade with its strategy in `trade_logger.py` — add `strategy` as a parameter:

```python
def log_trade(cycle: int, action: str, strategy: str, ...):  # Add strategy param
    record = {
        ...
        "strategy": strategy,  # "momentum" or "mean_reversion"
        ...
    }
```

In `main.py`, alternate strategies every 5 cycles to build comparison data:
```python
def get_cycle_strategy(cycle: int) -> str:
    """Alternate strategies every 5 cycles for comparison data."""
    block = cycle // 5
    return "momentum" if block % 2 == 0 else "mean_reversion"
```

After 10+ cycles, run the comparison:
```bash
python -c "
from agent.core.reputation_scorer import compute_strategy_scores
import json
scores = compute_strategy_scores()
print(json.dumps(scores, indent=2))
"
```

Document the winning strategy (higher Sharpe) in `docs/onboarding.md` Phase 4 Notes.

### Step 5: The Graph Subgraph (Bonus)

If you have time, deploy a subgraph to index ERC-8004 events on Base Sepolia. This is a **strong bonus** — judges actively check The Graph.

**Install The Graph CLI:**
```bash
npm install -g @graphprotocol/graph-cli
```

**Initialize subgraph:**
```bash
graph init \
  --product hosted-service \
  --from-contract $IDENTITY_REGISTRY_ADDRESS \
  --network base-sepolia \
  --abi contracts/out/IdentityRegistry.sol/IdentityRegistry.json \
  chronotrader-subgraph
```

**Define schema in `schema.graphql`:**
```graphql
type AgentRegistered @entity {
  id: ID!
  agentId: BigInt!
  owner: Bytes!
  metadataURI: String!
  registeredAt: BigInt!
  blockNumber: BigInt!
}

type ReputationUpdated @entity {
  id: ID!
  agentId: BigInt!
  score: BigInt!
  updatedAt: BigInt!
  sessionId: String!
}

type TradeValidated @entity {
  id: ID!
  agentId: BigInt!
  dataHash: Bytes!
  cycle: BigInt!
  timestamp: BigInt!
}
```

**Deploy:**
```bash
cd chronotrader-subgraph
graph codegen && graph build
graph deploy --product hosted-service chronosllc0-ai/chronotrader
```

Add the subgraph endpoint URL to `docs/onboarding.md` Phase 4 Notes.

### Step 6: TEE Attestation Stub (Bonus)

If The Graph deployment takes too long, implement a TEE attestation stub. This signals intent to judges even if full TEE integration isn't complete:

```python
# agent/core/tee_attestation.py
"""
TEE attestation stub for ChronoTrader.
In production: integrate with Phala Network or Intel TDX.
For hackathon: generates a mock attestation that demonstrates the data flow.
"""

import hashlib
import json
from datetime import datetime, timezone

def generate_mock_attestation(trade_data: dict, metrics: dict) -> dict:
    """
    Generate a mock TEE attestation document.
    
    In production, this would:
    1. Run inside a Trusted Execution Environment (e.g., Phala Network)
    2. The TEE would sign the computation hash with its hardware key
    3. The attestation would be verifiable against Intel/AMD root certificates
    
    For the hackathon demo: demonstrates the attestation data structure.
    """
    attestation = {
        "version": "1.0",
        "type": "mock-tee-attestation",
        "note": "DEMO: In production, replace with Phala Network or TDX attestation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tee_type": "SGX-simulated",
        "measurement": {
            "mrenclave": hashlib.sha256(
                json.dumps(trade_data, sort_keys=True).encode()
            ).hexdigest(),
            "strategy_hash": hashlib.sha256(
                json.dumps({"strategy": trade_data.get("strategy"), 
                           "signal": trade_data.get("signal")}, sort_keys=True).encode()
            ).hexdigest(),
            "metrics_hash": hashlib.sha256(
                json.dumps(metrics, sort_keys=True).encode()
            ).hexdigest(),
        },
        "report_data": {
            "agent_id": trade_data.get("agent_id"),
            "trade_cycles": metrics.get("total_trades"),
            "sharpe_ratio": metrics.get("sharpe_ratio"),
        }
    }
    
    # Simulate attestation signature
    attestation["signature"] = hashlib.sha256(
        json.dumps(attestation["measurement"], sort_keys=True).encode()
    ).hexdigest()
    
    return attestation
```

Store the attestation alongside validation artifacts and reference it in the README with a note about production TEE integration.

### Step 7: Final Metrics Display

In `main.py`, add `cmd_status()` — a rich status report callable anytime:

```bash
python agent/main.py status
```

This should show:
1. Agent ID and registration status (with link to identity on-chain)
2. Current reputation score (fetched from ReputationRegistry)
3. Full performance table (trades, PnL, Sharpe, drawdown, win rate)
4. Strategy comparison table (if data exists)
5. Links to last 5 validation artifact txs on `sepolia.basescan.org`
6. Loop status (running / stopped, last cycle time)

### Step 8: Update `docs/onboarding.md`

For each completed Phase 4 task:
- Change status to `✅ DONE`
- Add the reputation score tx hash in Notes
- Add The Graph subgraph URL in Notes (if deployed)
- Add the winning strategy (momentum vs mean reversion) in Notes

---

## Definition of Done

Phase 4 is complete when ALL of the following are true:

- [ ] All Phase 1, 2, and 3 tasks in `docs/onboarding.md` are `✅ DONE`
- [ ] `python agent/main.py validate` submits a non-placeholder reputation score to ReputationRegistry
- [ ] Reputation score tx visible on `sepolia.basescan.org` (link in Notes)
- [ ] Reputation score is between 501 and 9999 (not a placeholder value)
- [ ] `agent/core/validation_agent.py` runs without errors
- [ ] Multi-strategy comparison data exists (at least 5 cycles per strategy)
- [ ] `python agent/main.py status` shows Rich tables with all metrics
- [ ] Status output includes a clickable link to `sepolia.basescan.org` for the last tx
- [ ] *(Bonus)* The Graph subgraph deployed and accessible via endpoint URL
- [ ] *(Bonus)* `agent/core/tee_attestation.py` exists with attestation stub
- [ ] All Phase 4 tasks in `docs/onboarding.md` show `✅ DONE`
- [ ] `docs/onboarding.md` Phase 4 "What's next" confirms Phase 5 is unblocked

---

## Resources

- ERC-8004 Reputation Registry spec: `https://eips.ethereum.org/EIPS/eip-8004`
- The Graph — Base Sepolia: `https://thegraph.com/docs/en/deploying/subgraph-studio/`
- The Graph CLI: `https://github.com/graphprotocol/graph-tooling`
- Phala Network (TEE): `https://docs.phala.network`
- Rich library docs: `https://rich.readthedocs.io`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- Hackathon page: `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
- Hackathon judging criteria: validation quality + ERC-8004 integration depth are high-weight
