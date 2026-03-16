# ChronoTrader — Autonomous AI Trading Agent with ERC-8004 Trust

> **Trustless AI trading agents that earn reputation through verifiable on-chain performance.**

Built for the [AI Trading Agents with ERC-8004 Hackathon](https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004) (March 30 – April 12, 2026).

---

## Overview

ChronoTrader is an autonomous AI trading agent that uses **ERC-8004's on-chain trust layer** to register identity, execute DeFi strategies, and build verifiable reputation — all without centralized intermediaries.

### Core Capabilities

- **🪪 On-Chain Identity** — ERC-8004 registered agent with verifiable capabilities and strategy metadata
- **🧠 LLM-Powered Strategy** — CrewAI multi-agent system with GPT-4 reasoning for market analysis, risk assessment, and trade execution
- **⛓️ Trustless Execution** — Signed TradeIntents executed through the Risk Router with EIP-712 typed data
- **📈 Verifiable Reputation** — Performance metrics (PnL, Sharpe ratio, max drawdown) recorded on-chain via Reputation & Validation Registries
- **🔗 Agent Composability** — Discoverable by other ERC-8004 agents for multi-agent financial strategies

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CHRONOTRADER AGENT                     │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Strategy    │  │     Risk     │  │  Execution   │   │
│  │    Agent      │──│    Agent     │──│    Agent     │   │
│  │  (GPT-4 +    │  │  (Position   │  │  (On-chain   │   │
│  │   CrewAI)    │  │   Sizing)    │  │   Signing)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                  │                  │           │
│  ┌──────┴──────────────────┴──────────────────┴───────┐  │
│  │              Tool Layer                             │  │
│  │  Chainlink Feeds │ Uniswap Router │ ERC-8004 SDK   │  │
│  └─────────────────────────┬──────────────────────────┘  │
└────────────────────────────┼─────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────────┐
     │   Identity   │ │  Risk    │ │  Reputation  │
     │   Registry   │ │  Router  │ │  + Validation│
     │  (ERC-8004)  │ │(Sandbox) │ │  Registries  │
     └──────────────┘ └──────────┘ └──────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    Base Sepolia / Base
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Smart Contracts | Solidity + Foundry | ERC-8004 registries, TradeIntent, RiskManager |
| Agent Framework | CrewAI (Python) | Multi-agent orchestration with role-based agents |
| LLM | OpenAI GPT-4 | Strategy reasoning and market analysis |
| Blockchain | Base Sepolia → Base | ERC-8004's target L2, low gas for agent interactions |
| DEX | Uniswap V3 | Trade execution via whitelisted Risk Router |
| Oracles | Chainlink | Real-time price feeds |
| Indexing | The Graph | Discovery dashboards and leaderboards |
| Signatures | EIP-712 | Typed data for TradeIntent signing |
| Storage | IPFS | Agent cards and validation evidence |

---

## Project Structure

```
chronotrader/
├── contracts/                # Solidity smart contracts (Foundry)
│   ├── src/
│   │   ├── registries/       # ERC-8004 Identity, Reputation, Validation
│   │   ├── trading/          # TradeIntent, RiskManager, StrategyVault
│   │   └── interfaces/       # Contract interfaces
│   ├── script/               # Deployment scripts
│   ├── test/                 # Contract tests
│   └── foundry.toml
├── agent/                    # Python AI agent (CrewAI)
│   ├── core/                 # Agent definitions
│   │   ├── strategy_agent.py # LLM-powered trade reasoning
│   │   ├── risk_agent.py     # Position sizing & stop-loss
│   │   └── execution_agent.py# On-chain trade execution
│   ├── tools/                # Agent tools
│   │   ├── chainlink_feed.py # Price oracle integration
│   │   ├── uniswap_router.py # DEX execution
│   │   └── erc8004_registry.py # Registry interactions
│   ├── config/               # Agent configuration
│   └── main.py               # Entry point
├── frontend/                 # Dashboard (Next.js) — optional
├── subgraph/                 # The Graph indexer — optional
├── docs/                     # Documentation
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Foundry](https://book.getfoundry.sh/getting-started/installation) (forge, cast, anvil)
- Node.js 18+ (for frontend/subgraph)
- OpenAI API key
- Wallet with Base Sepolia ETH

### 1. Clone & Install

```bash
git clone https://github.com/chronosllc0-ai/chronotrader.git
cd chronotrader

# Install Python deps
cd agent && pip install -r requirements.txt && cd ..

# Install Foundry deps
cd contracts && forge install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and wallet
```

### 3. Deploy Contracts (Local)

```bash
# Start local chain
anvil --port 8545 &

# Deploy
cd contracts
forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast
```

### 4. Register Agent

```bash
cd agent
python main.py register
```

### 5. Run Trading Agent

```bash
python main.py trade --strategy momentum
```

---

## Hackathon Compliance

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| ERC-8004 Identity Registry | ✅ | Agent mints ERC-721 identity with capabilities metadata |
| Reputation accumulation | ✅ | Objective PnL + validator scores feed reputation |
| Validation artifacts | ✅ | Trade intents, risk checks, strategy checkpoints |
| Hackathon Capital Sandbox | ✅ | Operates through provided vault + Risk Router |
| EIP-712 TradeIntents | ✅ | Typed data signatures for all trade submissions |
| Risk-adjusted profitability | ✅ | Sharpe ratio, max drawdown, sortino optimization |

---

## Team

**Chronos Intelligence Systems** — AI agent infrastructure company building the platform for autonomous, composable AI systems.

- **Jesse Newton Okoroma** — Founder & CEO. LLM engineer and AI architect with deep expertise in agentic system design, multi-agent orchestration, and deploying AI into finance and trading.

---

## License

MIT
