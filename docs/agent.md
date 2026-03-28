# ChronoTrader — Agent Architecture

> Deep-dive into how the AI agent system works, how to run it locally, and how to extend it.

---

## Overview

ChronoTrader uses **CrewAI** to orchestrate a 3-agent pipeline that mimics a professional trading desk: a strategist who reads the market, a risk officer who controls exposure, and an execution specialist who submits trades on-chain. Each agent has a specific role, toolset, and decision boundary.

```
Market Data (Chainlink)
        │
        ▼
┌───────────────────┐
│  Strategy Agent   │  ← GPT-4, temp=0.1 (some creativity for analysis)
│  Senior Strategist│  Tools: get_token_price, get_market_summary, check_reputation
│                   │  Output: JSON trade signal (action, entry, stop, target, size%)
└────────┬──────────┘
         │ trade signal
         ▼
┌───────────────────┐
│    Risk Agent     │  ← GPT-4, temp=0.0 (deterministic, no creativity)
│  Chief Risk Officer│  Tools: get_token_price, check_balance
│                   │  Output: APPROVED/REJECTED + adjusted_position_size + risk_score
└────────┬──────────┘
         │ approved trade (or REJECTED → stop)
         ▼
┌───────────────────┐
│  Execution Agent  │  ← GPT-4, temp=0.0 (deterministic)
│  Exec Specialist  │  Tools: execute_swap, check_balance, register_agent, check_reputation
│                   │  Output: tx_hash, amount_out, validation_hash
└────────┬──────────┘
         │
         ▼
  ERC-8004 Registries (Base Sepolia)
  IdentityRegistry → ReputationRegistry → ValidationRegistry
```

---

## Agent Definitions

### 1. Strategy Agent (`agent/core/strategy_agent.py`)

**Role:** Senior Trading Strategist  
**LLM:** GPT-4, temperature=0.1  
**Decision boundary:** Generates signals, never touches money

The Strategy Agent reads live market data (Chainlink price feeds), checks reputation of peer agents (ERC-8004), and produces a structured JSON trade signal. It must recommend a specific action (BUY/SELL/HOLD) with entry price, stop-loss (max 3% from entry), take-profit targets, position size as % of capital (max 20%), and a confidence score.

Key design choice: **temperature=0.1** — slight randomness allows it to notice different market aspects across cycles, but not enough to produce wild or inconsistent reasoning.

**Available tools:**
- `get_token_price(token_symbol)` — Chainlink price feed query
- `get_market_summary(token_symbol)` — Multi-timeframe summary
- `check_reputation(agent_id)` — Check peer agent reputation on ERC-8004

**Output format (JSON):**
```json
{
  "trend_assessment": "bullish",
  "confidence_level": 7,
  "recommended_action": "BUY",
  "entry_price": 3450.00,
  "stop_loss": 3346.50,
  "take_profit": [3550.00, 3650.00],
  "position_size_pct": 12.5,
  "risk_reward_ratio": 2.4,
  "rationale": "Strong momentum above 20-day EMA, Chainlink feed confirmed..."
}
```

---

### 2. Risk Agent (`agent/core/risk_agent.py`)

**Role:** Chief Risk Officer  
**LLM:** GPT-4, temperature=0.0  
**Decision boundary:** Approves or rejects trades, can reduce position size, cannot execute

The Risk Agent is the gatekeeper. It receives the Strategy Agent's signal and validates it against hard risk limits. It never trusts the Strategy Agent's self-reported position size — it independently checks current balances and enforces:

| Parameter | Default | Configurable via |
|-----------|---------|-----------------|
| Max position size | 20% of capital | `MAX_POSITION_SIZE_USD` in `.env` |
| Max daily loss | 5% | `MAX_DAILY_LOSS_PCT` in `.env` |
| Max drawdown | 15% | `MAX_DRAWDOWN_PCT` in `.env` |
| Min risk/reward | 2:1 | Hardcoded in task |
| Max slippage | 1% | Hardcoded in task |

**Key design choice:** temperature=0.0 — risk decisions must be deterministic and reproducible. The same input must always produce the same output for audit purposes.

**Output format (JSON):**
```json
{
  "approved": true,
  "adjusted_position_size": 10.0,
  "risk_score": 3,
  "warnings": ["Position size reduced from 12.5% to 10% due to current drawdown"],
  "reasoning": "Trade meets all risk criteria. Stop-loss is 3% from entry..."
}
```

---

### 3. Execution Agent (`agent/core/execution_agent.py`)

**Role:** Execution Specialist  
**LLM:** GPT-4, temperature=0.0  
**Decision boundary:** Submits on-chain transactions only after risk approval

The Execution Agent turns approved trade signals into on-chain reality. It:
1. Verifies current balances haven't changed since risk check
2. Confirms prices haven't moved beyond acceptable deviation
3. Signs a `TradeIntent` using EIP-712 (`eip712_signer.py`)
4. Submits the signed intent to the Hackathon Capital Risk Router
5. Verifies the transaction succeeded and output meets minimum requirements
6. Hashes the full trade cycle data and submits to ValidationRegistry
7. Updates performance metrics for reputation calculation

**Critical:** If prices have moved more than 0.5% from the risk-check price, the Execution Agent must abort and NOT execute. Stale approvals are dangerous.

---

## Tool Layer (`agent/tools/`)

### `chainlink_feed.py`
Reads live price data from Chainlink Data Feeds on Base Sepolia.

```python
from agent.tools import get_token_price, get_market_summary

price = get_token_price("ETH")     # Returns float USD price
summary = get_market_summary("ETH")  # Returns dict with price, volume, change
```

Chainlink Base Sepolia feed addresses:
- ETH/USD: `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1`
- BTC/USD: `0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298`
- USDC/USD: `0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165`

### `eip712_signer.py`
Signs `TradeIntent` structs using EIP-712 typed data.

```python
from agent.tools.eip712_signer import TradeIntentData, sign_trade_intent

intent = TradeIntentData(
    agent_id=1,
    token_in="0x...",    # WETH address
    token_out="0x...",   # USDC address
    amount_in=int(0.1 * 1e18),   # 0.1 ETH in wei
    min_amount_out=int(340 * 1e6),  # 340 USDC min (6 decimals)
    deadline=int(time.time()) + 1800,  # 30 min
    nonce=0,
    strategy_hash=b'\x00' * 32,
)

signed = sign_trade_intent(
    intent=intent,
    private_key=os.getenv("AGENT_PRIVATE_KEY"),
    verifying_contract=RISK_ROUTER_ADDRESS,
    chain_id=84532,  # Base Sepolia
)
# Returns: {"v": int, "r": hex, "s": hex, "signature": hex, "intent": dict}
```

### `erc8004_registry.py`
Interacts with ERC-8004 Identity, Reputation, and Validation registries.

```python
from agent.tools import register_agent, check_reputation

# Register agent (Phase 1)
agent_id = register_agent("ipfs://Qm.../agent_card.json")

# Check reputation (any phase)
rep = check_reputation(agent_id=1)
# Returns: {"total": int, "count": int, "average": int}
```

### `uniswap_router.py`
Submits signed TradeIntents to the Hackathon Capital Risk Router (wraps Uniswap V3).

```python
from agent.tools import execute_swap

result = execute_swap(
    token_in="0x...",
    token_out="0x...",
    amount_in=int(0.1 * 1e18),
    min_amount_out=int(340 * 1e6),
    signed_intent=signed,  # from eip712_signer
)
# Returns: {"tx_hash": "0x...", "amount_out": int, "gas_used": int}
```

---

## Contract Architecture (`contracts/src/`)

### Registries

**`IdentityRegistry.sol`** — ERC-721 extended for agents  
- `register(uri)` → agentId (uint256)  
- `tokenURI(agentId)` → IPFS URI of agent card JSON  
- `ownerOfAgent(agentId)` → owner address  

**`ReputationRegistry.sol`** — Weighted score accumulator  
- `submitFeedback(serverAgentId, score, metadata)` — validators call this  
- `getReputation(agentId)` → (total, count, average)  

**`ValidationRegistry.sol`** — Audit trail for trade cycles  
- `validationRequest(validatorAgentId, serverAgentId, dataHash)` — submit artifact  
- `getValidation(dataHash)` → validation struct  

### Trading

**`TradeIntent.sol`** — EIP-712 typed data definition  
Defines the `TradeIntent` struct and domain separator for signing. Includes nonce tracking and deadline enforcement.

**`RiskManager.sol`** — On-chain risk enforcement  
Validates position sizes, daily loss limits, and drawdown limits before allowing trade execution. The hackathon sandbox Risk Router uses this.

**`StrategyVault.sol`** — Capital management vault  
The Hackathon Capital Sandbox vault. All trading capital flows through this. Enforces risk parameters set by RiskManager.

---

## Running Locally

### Prerequisites

```bash
# Python 3.10+
python --version

# Foundry (forge + cast + anvil)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Node 18+ (for subgraph/frontend, optional)
node --version
```

### Install Dependencies

```bash
git clone https://github.com/chronosllc0-ai/Chronotrader.git
cd Chronotrader

# Python agent deps
cd agent && pip install -r requirements.txt && cd ..

# Solidity deps
cd contracts && forge install && cd ..
```

### Environment Setup

```bash
cp .env.example .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-...          # Required for all agent operations
AGENT_PRIVATE_KEY=0x...        # Funded wallet (Base Sepolia ETH)
NETWORK=local                  # Start with local, switch to base_sepolia after deploy
```

### Local Development (Anvil)

```bash
# Terminal 1: Start local chain
anvil --port 8545 --chain-id 31337 &

# Terminal 2: Deploy contracts
cd contracts
forge script script/Deploy.s.sol \
  --rpc-url http://localhost:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Copy deployed addresses to .env
# IDENTITY_REGISTRY_ADDRESS=0x...
# REPUTATION_REGISTRY_ADDRESS=0x...
# etc.

# Register agent
cd ..
python agent/main.py register

# Single trade cycle
python agent/main.py trade

# Continuous loop (15-min intervals)
python agent/main.py loop
```

### Deploy to Base Sepolia

```bash
# Set network in .env
NETWORK=base_sepolia

# Deploy (uses BASE_SEPOLIA_RPC_URL from .env)
cd contracts
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.base.org \
  --broadcast \
  --verify \
  --etherscan-api-key $BASESCAN_API_KEY

# Update .env with real Base Sepolia addresses
# Run agent against testnet
cd ..
python agent/main.py register
python agent/main.py loop
```

---

## Agent Configuration Reference

All agent behavior is controlled via `.env` variables, loaded by `agent/config/settings.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4` | LLM model (gpt-4, gpt-4-turbo) |
| `MAX_POSITION_SIZE_USD` | `1000.0` | Max USD value per position |
| `MAX_DAILY_LOSS_PCT` | `5.0` | Daily loss limit as % of capital |
| `MAX_DRAWDOWN_PCT` | `15.0` | Max portfolio drawdown |
| `DEFAULT_STRATEGY` | `momentum` | Default strategy (momentum/mean_reversion) |
| `NETWORK` | `local` | Target network (local/base_sepolia) |
| `IPFS_GATEWAY` | `https://ipfs.io/ipfs/` | IPFS gateway for agent cards |

---

## Adding a New Strategy

1. Create a new task function in `agent/core/strategy_agent.py`:
```python
def create_yield_strategy_task(agent: Agent) -> Task:
    return Task(
        description="Analyze yield opportunities across Aave V3 and Uniswap V3 LP...",
        expected_output="JSON with optimal yield position...",
        agent=agent,
    )
```

2. Register it in `main.py` under `cmd_trade()`:
```python
if settings.default_strategy == "yield_optimization":
    analysis_task = create_yield_strategy_task(strategy_agent)
```

3. Add the strategy name to the agent card capabilities in `create_agent_card()`.

---

## Validation Artifact Format

Every trade cycle produces a validation artifact — a SHA-256 hash of the full cycle data. This is submitted to ValidationRegistry for auditing.

```python
cycle_data = {
    "agent_id": 1,
    "timestamp": int(time.time()),
    "strategy": "momentum",
    "analysis": {...},       # Strategy agent output
    "risk_check": {...},     # Risk agent output
    "execution": {...},      # Execution agent output (tx_hash, etc.)
    "performance": {
        "pnl_usd": 12.50,
        "sharpe_contribution": 0.15,
        "drawdown_used_pct": 2.3,
    }
}
data_hash = hashlib.sha256(json.dumps(cycle_data, sort_keys=True).encode()).hexdigest()
# Submit 0x{data_hash} to ValidationRegistry
```

---

## Debugging

### Check agent registration
```bash
cast call $IDENTITY_REGISTRY_ADDRESS "agentCount()(uint256)" --rpc-url https://sepolia.base.org
cast call $IDENTITY_REGISTRY_ADDRESS "tokenURI(uint256)(string)" 1 --rpc-url https://sepolia.base.org
```

### Check reputation score
```bash
cast call $REPUTATION_REGISTRY_ADDRESS "getReputation(uint256)(uint256,uint256,uint256)" 1 --rpc-url https://sepolia.base.org
```

### Check validation artifacts
```bash
cast call $VALIDATION_REGISTRY_ADDRESS "getValidation(bytes32)(...)" 0x{DATA_HASH} --rpc-url https://sepolia.base.org
```

### View recent transactions
```
https://sepolia.basescan.org/address/{AGENT_WALLET_ADDRESS}
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `forge: command not found` | Foundry not installed | Run `foundryup` |
| `insufficient funds` | Wallet needs Base Sepolia ETH | Use faucet at coinbase.com/faucets |
| `nonce too low` | Pending tx from previous run | Increase nonce or reset with `cast nonce` |
| `execution reverted` on swap | Slippage or wrong min_amount_out | Reduce min_amount_out or increase deadline |
| `OPENAI_API_KEY not set` | Missing .env value | Add key to .env file |
| CrewAI tool error | Tool not initialized | Call `init_tools()` before creating agents |
