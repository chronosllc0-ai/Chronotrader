# Codex Prompt — Phase 2: Trading Core
**Days 4–6 | April 2–4, 2026**  
**Goal:** End-to-end trade flow working — strategy signal → risk check → EIP-712 signed TradeIntent → Risk Router submission

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now.**

Open `docs/onboarding.md` and check:
1. **Phase 1 tasks** — are all statuses `✅ DONE`? If any are `⬜ TODO` or `🔄 IN PROGRESS`, **finish those first** before starting Phase 2 work. Phase 2 cannot function without deployed contracts and a registered agent.
2. **Phase 1 "What's next" line** — confirms Phase 2 is unblocked (TradeIntent signing, Risk Router, strategy engine)
3. **Phase 2 task table** — check which tasks are already done (if resuming mid-phase)
4. **Notes column in Phase 1** — get the contract addresses, Agent ID, and IPFS URI that were set up

**Step 2 — If Phase 1 has incomplete tasks, finish them before proceeding.** Do not start Phase 2 work with a partially complete Phase 1. Specifically:
- You NEED `IDENTITY_REGISTRY_ADDRESS` and `AGENT_ID` in `.env` (from Phase 1 Step 5)
- You NEED `RISK_ROUTER_ADDRESS` and `SANDBOX_VAULT_ADDRESS` (obtain from hackathon docs)
- You NEED the wallet to have Base Sepolia ETH for gas

**Step 3 — Update `docs/onboarding.md` Phase 2 task table as you complete each task.**

---

## Context

Phase 1 gave you: deployed contracts on Base Sepolia, a registered agent with an on-chain ID.

Phase 2 is the **trading engine** — making the agent actually trade. This means:
1. The Strategy Agent generates a real trade signal from Chainlink data
2. The Risk Agent validates it against on-chain limits
3. The Execution Agent builds a valid `TradeIntent`, signs it with EIP-712, and submits it to the Hackathon Capital Risk Router
4. The full cycle is testable end-to-end with `python agent/main.py trade`

The most critical piece: **the EIP-712 signing pipeline must produce signatures that the Risk Router on-chain contract accepts.** This requires matching the exact domain separator and struct hash that the RiskManager contract uses.

---

## Goal

By the end of Phase 2, **all of the following must be true:**
1. Hackathon Capital Sandbox vault and Risk Router addresses obtained and in `.env`
2. `eip712_signer.py` produces valid signatures accepted by on-chain RiskManager
3. `uniswap_router.py` submits TradeIntents to the sandbox Risk Router
4. Strategy Agent produces valid structured JSON signals (BUY/SELL/HOLD) from live Chainlink data
5. Risk Agent correctly approves/rejects trades against configured limits
6. Execution Agent successfully submits signed intents and records validation hashes
7. `python agent/main.py trade` completes a full cycle without error (on Base Sepolia)

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` FIRST. Finish any incomplete Phase 1 tasks before starting Phase 2.**
- [ ] Get hackathon sandbox contract addresses from the official hackathon docs/Discord and add to `.env` as `SANDBOX_VAULT_ADDRESS` and `SANDBOX_RISK_ROUTER_ADDRESS`
- [ ] The EIP-712 domain separator in `eip712_signer.py` MUST match the one in `RiskManager.sol` exactly (same `name`, `version`, `chainId`, `verifyingContract`)
- [ ] Every TradeIntent MUST include a valid `strategyHash` — SHA-256 of the strategy agent's analysis JSON
- [ ] Deadlines MUST be enforced — reject any intent where `deadline < block.timestamp + 60` (at least 60 seconds remaining)
- [ ] After each trade cycle, hash the full cycle data and record it to ValidationRegistry
- [ ] Write a `agent/metrics.py` module that calculates: PnL (USD), Sharpe ratio contribution, max drawdown so far
- [ ] Update `docs/onboarding.md` Phase 2 task table as each task completes

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** start Phase 2 work if Phase 1 has incomplete tasks — fix Phase 1 first
- [ ] **MUST NOT** hardcode the Risk Router address — must come from `.env`
- [ ] **MUST NOT** submit TradeIntents with `minAmountOut = 0` — always calculate from live Chainlink price with ≥0.5% slippage buffer
- [ ] **MUST NOT** execute trades if the current price has moved more than 1% from the risk-check price
- [ ] **MUST NOT** allow the Risk Agent to be bypassed — execution MUST check for "APPROVED" in risk output
- [ ] **MUST NOT** skip validation artifact recording — every trade cycle, even failed ones, must produce a hash stored somewhere
- [ ] **MUST NOT** use hardcoded gas limits — let web3.py estimate gas and add 20% buffer

---

## Implementation Steps

### Step 1: Obtain Hackathon Sandbox Addresses

Check the official hackathon documentation at `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004` and the hackathon Discord for:
- Hackathon Capital Sandbox vault address (Base Sepolia)
- Risk Router contract address (Base Sepolia)
- Any API endpoints for the sandbox

Add to `.env`:
```bash
SANDBOX_VAULT_ADDRESS=0x...
SANDBOX_RISK_ROUTER_ADDRESS=0x...
```

If sandbox addresses aren't published yet, use a local fork of Base Sepolia:
```bash
anvil --fork-url https://sepolia.base.org --port 8545
```
And proceed with local testing — but mark these tasks as `🔄 IN PROGRESS` in `docs/onboarding.md`.

### Step 2: Align EIP-712 Domain Separator

Open `contracts/src/trading/TradeIntent.sol` and find the domain separator definition. It should look like:

```solidity
bytes32 private constant DOMAIN_TYPEHASH = keccak256(
    "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
);
```

Now open `agent/tools/eip712_signer.py` and ensure `build_eip712_message()` uses **identical** values:
- `name` must match exactly (case-sensitive)
- `version` must match exactly
- `chainId` must be `84532` for Base Sepolia (not hardcoded — read from web3.eth.chain_id)
- `verifyingContract` must be the Risk Router address from `.env`

Write a test: sign an intent off-chain, then verify it using `cast`:
```bash
cast call $SANDBOX_RISK_ROUTER_ADDRESS \
  "verifyTradeIntent((uint256,address,address,uint256,uint256,uint256,uint256,bytes32),bytes)(bool)" \
  "($AGENT_ID,$TOKEN_IN,$TOKEN_OUT,$AMOUNT_IN,$MIN_OUT,$DEADLINE,$NONCE,$STRATEGY_HASH)" \
  "$SIGNATURE" \
  --rpc-url https://sepolia.base.org
```
If this returns `true`, your signing is correct.

### Step 3: Fix `uniswap_router.py` — Risk Router Integration

Current `uniswap_router.py` has a commented-out `TODO` in `main.py`. Implement the Risk Router submission:

```python
# In agent/tools/uniswap_router.py

from agent.tools.eip712_signer import TradeIntentData, sign_trade_intent

RISK_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "intent", "type": "tuple", "components": [
                {"name": "agentId", "type": "uint256"},
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "minAmountOut", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "strategyHash", "type": "bytes32"},
            ]},
            {"name": "signature", "type": "bytes"},
        ],
        "name": "executeIntent",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def submit_trade_intent(intent: TradeIntentData, signature: bytes, w3: Web3, private_key: str, router_address: str) -> dict:
    """Submit a signed TradeIntent to the Risk Router"""
    # Build and send transaction
    # Return: {tx_hash, amount_out, gas_used, success}
```

The `execute_swap` CrewAI tool in `tools/__init__.py` should call this function.

### Step 4: Verify Strategy Agent Output Format

Run the Strategy Agent in isolation and check its JSON output is parseable:

```python
# test_strategy.py (temporary, delete after)
import os
from dotenv import load_dotenv
load_dotenv()
from agent.core.strategy_agent import create_strategy_agent, create_market_analysis_task
from crewai import Crew, Process

agent = create_strategy_agent(os.getenv("OPENAI_API_KEY"))
task = create_market_analysis_task(agent, "Strategy: momentum, Capital: $1000")
crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
result = crew.kickoff()
print(result)

# Verify it's valid JSON with required fields
import json
data = json.loads(str(result))
assert "recommended_action" in data
assert data["recommended_action"] in ["BUY", "SELL", "HOLD"]
assert "position_size_pct" in data
assert data["position_size_pct"] <= 20  # Hard limit
```

If the output isn't valid JSON, modify the task description to be more explicit:
```python
"CRITICAL: Your ENTIRE response must be a single valid JSON object. No markdown, no explanation, no code blocks. Start with { and end with }."
```

### Step 5: Implement `agent/metrics.py`

Create a performance tracking module:

```python
# agent/metrics.py

import json
import math
from pathlib import Path
from datetime import datetime

METRICS_FILE = Path(__file__).parent / "data" / "performance.json"

def load_metrics() -> dict:
    """Load existing performance metrics"""
    if METRICS_FILE.exists():
        return json.loads(METRICS_FILE.read_text())
    return {
        "total_trades": 0,
        "winning_trades": 0,
        "total_pnl_usd": 0.0,
        "returns": [],          # List of per-trade return %
        "peak_capital": 1000.0,
        "current_capital": 1000.0,
        "max_drawdown_pct": 0.0,
        "trade_history": []
    }

def update_metrics(trade_result: dict, amount_in_usd: float, amount_out_usd: float) -> dict:
    """Update metrics after a trade and recalculate Sharpe/drawdown"""
    metrics = load_metrics()
    
    pnl = amount_out_usd - amount_in_usd
    return_pct = (pnl / amount_in_usd) * 100 if amount_in_usd > 0 else 0
    
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
    
    # Calculate Sharpe ratio (annualized, assuming 15-min cycles → ~35,000 cycles/year)
    if len(metrics["returns"]) >= 2:
        avg_return = sum(metrics["returns"]) / len(metrics["returns"])
        std_return = math.sqrt(sum((r - avg_return)**2 for r in metrics["returns"]) / len(metrics["returns"]))
        if std_return > 0:
            # Annualize: sqrt(35040 cycles per year for 15-min cycles)
            metrics["sharpe_ratio"] = (avg_return / std_return) * math.sqrt(35040)
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
    
    METRICS_FILE.parent.mkdir(exist_ok=True)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2))
    return metrics

def print_metrics_summary(metrics: dict):
    """Print a rich summary of current performance"""
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
```

### Step 6: Wire Everything Together in `main.py`

In `cmd_trade()`, after the execution step:
1. Calculate PnL from amount_in vs amount_out (using Chainlink for USD conversion)
2. Call `update_metrics(exec_result, amount_in_usd, amount_out_usd)`
3. Print the metrics summary with `print_metrics_summary(metrics)`
4. Hash the full cycle data and submit to ValidationRegistry

Also: uncomment the Uniswap router initialization in `init_tools()` and point it to the sandbox Risk Router:
```python
init_uniswap_tools(
    rpc_url=settings.rpc_url,
    private_key=settings.agent_private_key,
    router_address=settings.sandbox_risk_router_address,
)
```

### Step 7: End-to-End Test

Run a full trade cycle:
```bash
NETWORK=base_sepolia python agent/main.py trade
```

The output should show:
1. Tool clients initialized (ERC-8004, Chainlink, Uniswap)
2. Strategy Agent analyzing market, producing JSON signal
3. Risk Agent running checklist, returning APPROVED or REJECTED
4. (If APPROVED) Execution Agent signing TradeIntent and submitting
5. Transaction hash logged
6. Validation artifact hash logged
7. Performance metrics table displayed

---

## Definition of Done

Phase 2 is complete when ALL of the following are true:

- [ ] All Phase 1 tasks in `docs/onboarding.md` are `✅ DONE`
- [ ] `SANDBOX_VAULT_ADDRESS` and `SANDBOX_RISK_ROUTER_ADDRESS` in `.env`
- [ ] EIP-712 signature verification test passes (cast call returns true)
- [ ] `python agent/main.py trade` completes a full cycle on Base Sepolia without unhandled errors
- [ ] At least one successful trade with a real tx hash on `sepolia.basescan.org`
- [ ] `agent/data/performance.json` exists and has correct metrics after the trade
- [ ] ValidationRegistry has at least one artifact hash from the trade cycle
- [ ] All Phase 2 tasks in `docs/onboarding.md` show `✅ DONE`
- [ ] `docs/onboarding.md` Phase 2 "What's next" confirms Phase 3 is unblocked

---

## Resources

- Hackathon Capital Sandbox docs: check hackathon Discord / lablab.ai
- EIP-712 specification: `https://eips.ethereum.org/EIPS/eip-712`
- Chainlink Base Sepolia feeds: `https://docs.chain.link/data-feeds/price-feeds/addresses?network=base-sepolia`
- web3.py EIP-712: `from eth_account.messages import encode_structured_data`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- Uniswap V3 Base Sepolia router: `0x2626664c2603336E57B271c5C0b26F421741e481`
