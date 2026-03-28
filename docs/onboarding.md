# ChronoTrader — Project Onboarding

> **Hackathon:** AI Trading Agents with ERC-8004 · March 30 – April 12, 2026  
> **Platform:** Base Sepolia testnet  
> **Team:** Chronos Intelligence Systems — Jesse Newton Okoroma  
> **Repo:** [chronosllc0-ai/Chronotrader](https://github.com/chronosllc0-ai/Chronotrader)

---

## What Is ChronoTrader?

ChronoTrader is an autonomous AI trading agent that uses **ERC-8004's on-chain trust layer** to register its identity, execute DeFi strategies with EIP-712 signed TradeIntents, and build verifiable on-chain reputation based on actual performance. No centralized intermediaries. Every decision is auditable, every trade is signed, every reputation point is earned.

The core innovation: **AI agents should have to prove they're trustworthy through verifiable on-chain performance, not just claims.** ERC-8004 makes that possible.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Smart Contracts | Solidity + Foundry | ERC-8004 registries, TradeIntent, RiskManager |
| Agent Framework | CrewAI (Python) | 3-agent system: Strategy → Risk → Execution |
| LLM | OpenAI GPT-4 | Strategy reasoning and market analysis |
| Blockchain | Base Sepolia | ERC-8004 L2, low gas, fast finality |
| DEX | Uniswap V3 (via Risk Router) | Trade execution via hackathon sandbox |
| Oracles | Chainlink | Real-time ETH/BTC/USDC price feeds |
| Indexing | The Graph | Discovery dashboards + leaderboards (bonus) |
| Signatures | EIP-712 | TradeIntent typed data signing |
| Storage | IPFS | Agent cards and validation evidence |

---

## Repository Structure

```
chronotrader/
├── contracts/                # Solidity smart contracts (Foundry)
│   ├── src/
│   │   ├── registries/       # IdentityRegistry, ReputationRegistry, ValidationRegistry
│   │   ├── trading/          # TradeIntent, RiskManager, StrategyVault
│   │   └── interfaces/       # IIdentityRegistry, IReputationRegistry, IValidationRegistry
│   ├── script/               # Deploy.s.sol
│   └── test/                 # IdentityRegistry.t.sol, RiskManager.t.sol, TradeIntent.t.sol
├── agent/                    # Python AI agent (CrewAI)
│   ├── core/                 # strategy_agent.py, risk_agent.py, execution_agent.py
│   ├── tools/                # chainlink_feed.py, eip712_signer.py, erc8004_registry.py, uniswap_router.py
│   ├── config/               # settings.py (pydantic-settings)
│   └── main.py               # CLI: register | trade | loop
├── docs/
│   ├── onboarding.md         # THIS FILE — project overview + phase tracker
│   ├── agent.md              # Agent architecture + local setup
│   └── codex/                # Codex prompt pack (phase1–5)
└── README.md
```

---

## Hackathon Judging Criteria

| Criterion | Weight | What Judges Look For |
|-----------|--------|---------------------|
| Risk-Adjusted Profitability | High | Sharpe ratio > 1.0, drawdown < 15%, consistent returns |
| Drawdown Control | High | Max drawdown enforced on-chain via RiskManager |
| Validation Quality | High | Rich validation artifacts, validator attestations, data hashes |
| ERC-8004 Integration Depth | High | Identity + Reputation + Validation all used meaningfully |
| Innovation | Medium | Novel strategy, composability, TEE/zkML/subgraph bonuses |

**Mandatory Requirements:**
- ✅ ERC-8004 Identity Registry — agent registers with capabilities metadata
- ✅ ERC-8004 Reputation Registry — performance scores accumulate on-chain
- ✅ ERC-8004 Validation Registry — trade intents submitted as validation artifacts
- ✅ Hackathon Capital Sandbox — all trades go through provided vault + Risk Router
- ✅ EIP-712 signed TradeIntents — all trade submissions use typed data signatures
- ✅ Risk-Adjusted Optimization — Sharpe ratio, drawdown, sortino tracked

**Bonus (aim for all 3):**
- ⬜ TEE attestations — verifiable compute proofs for strategy execution
- ⬜ The Graph subgraph — indexing for discovery dashboards
- ⬜ zkML — zero-knowledge proofs for strategy confidentiality

---

## 14-Day Sprint Plan

### Phase 1 — Foundation (Days 1–3, Mar 30 – Apr 1)
**Goal:** Working contracts deployed on Base Sepolia, agent registered on ERC-8004

| Task | Status | Notes |
|------|--------|-------|
| Contracts compile cleanly with `forge build` | ⬜ TODO | |
| All 3 contract tests pass (`forge test`) | ⬜ TODO | |
| Deploy to Base Sepolia with `forge script` | ⬜ TODO | |
| Contract addresses written to `.env` | ⬜ TODO | |
| Agent card JSON created and pinned to IPFS | ⬜ TODO | |
| Agent registered on IdentityRegistry | ⬜ TODO | Agent ID obtained |
| Registration verified on-chain | ⬜ TODO | |

**What's next after Phase 1:** Phase 2 — Trading Core (TradeIntent signing, Risk Router, strategy engine)

---

### Phase 2 — Trading Core (Days 4–6, Apr 2–4)
**Goal:** End-to-end trade flow: strategy signal → risk check → EIP-712 signed TradeIntent → Risk Router submission

| Task | Status | Notes |
|------|--------|-------|
| Connect Hackathon Capital Sandbox vault + Risk Router | ⬜ TODO | Get sandbox addresses from hackathon docs |
| EIP-712 TradeIntent signing working end-to-end | ⬜ TODO | `eip712_signer.py` complete |
| Risk Router submission function implemented | ⬜ TODO | `uniswap_router.py` connects to sandbox router |
| Strategy Agent produces valid JSON trade signals | ⬜ TODO | Momentum + mean reversion strategies |
| Risk Agent validates and size-adjusts positions | ⬜ TODO | Enforces max 20% position, 5% daily loss, 15% drawdown |
| Execution Agent submits signed TradeIntents | ⬜ TODO | Records validation artifact hash |
| Full trade cycle test (local Anvil or Sepolia fork) | ⬜ TODO | `python main.py trade` works |

**What's next after Phase 2:** Phase 3 — Live Execution (real trades on Hackathon Capital Sandbox, trust signals)

---

### Phase 3 — Live Execution (Days 7–9, Apr 5–7)
**Goal:** Agent executing real trades on Hackathon Capital Sandbox, emitting validation artifacts

| Task | Status | Notes |
|------|--------|-------|
| First live trade executed on Base Sepolia sandbox | ⬜ TODO | Transaction hash logged |
| Validation artifacts submitted to ValidationRegistry | ⬜ TODO | One hash per trade cycle |
| Continuous trading loop running (`python main.py loop`) | ⬜ TODO | 15-min cycle, error-resilient |
| Trade history logging to disk (JSON + CSV) | ⬜ TODO | For reputation calculations |
| Performance metrics computed (PnL, Sharpe, drawdown) | ⬜ TODO | `metrics.py` module |
| Chainlink feeds integrated for live price data | ⬜ TODO | ETH/USD, BTC/USD |
| Error handling + retry logic for failed tx | ⬜ TODO | Nonce management, gas escalation |

**What's next after Phase 3:** Phase 4 — Trust & Reputation (validators score performance, on-chain reputation)

---

### Phase 4 — Trust & Reputation (Days 10–11, Apr 8–9)
**Goal:** Reputation accumulating on-chain, validator scoring working, TEE/Graph bonus targets

| Task | Status | Notes |
|------|--------|-------|
| Reputation scores submitted to ReputationRegistry | ⬜ TODO | After each trading session |
| Validator feedback loop implemented | ⬜ TODO | `validation_agent.py` or cron script |
| Performance metrics displayed in-terminal + on-chain | ⬜ TODO | Rich tables, tx explorer links |
| The Graph subgraph deployed (bonus) | ⬜ TODO | Index Identity + Reputation events |
| TEE attestation stub or integration (bonus) | ⬜ TODO | Phala/TDX or mock attestation |
| Multi-strategy comparison (momentum vs mean reversion) | ⬜ TODO | Sharpe ratio comparison |

**What's next after Phase 4:** Phase 5 — Polish & Submit (dashboard, README, Devpost)

---

### Phase 5 — Polish & Submit (Days 12–14, Apr 10–12)
**Goal:** Submission-ready — clean README, Devpost page, demo video, live dashboard

| Task | Status | Notes |
|------|--------|-------|
| README updated with deployed contract addresses | ⬜ TODO | All addresses on Base Sepolia |
| Demo script written for 3-min video | ⬜ TODO | `docs/demo_script.md` |
| Demo video recorded (Loom or screen capture) | ⬜ TODO | Show: register → trade → reputation |
| Devpost submission text written | ⬜ TODO | What it does, how it works, what's built |
| Frontend dashboard (optional, Next.js) | ⬜ TODO | Reputation score + trade history |
| Final contract addresses in README + .env.example | ⬜ TODO | |
| Submitted to Devpost before Apr 12 deadline | ⬜ TODO | |

---

## Environment Variables

See `.env.example` for full list. Critical variables:

```bash
OPENAI_API_KEY=           # GPT-4 access
AGENT_PRIVATE_KEY=        # Wallet for signing (fund with Base Sepolia ETH)
NETWORK=base_sepolia      # Set after Phase 1 contracts deployed

# Populated after Phase 1 deploy:
IDENTITY_REGISTRY_ADDRESS=
REPUTATION_REGISTRY_ADDRESS=
VALIDATION_REGISTRY_ADDRESS=
RISK_ROUTER_ADDRESS=

# Populated after Phase 2 sandbox setup:
SANDBOX_VAULT_ADDRESS=
SANDBOX_RISK_ROUTER_ADDRESS=
```

---

## Getting Base Sepolia ETH

- Faucet: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
- Bridge: https://bridge.base.org (Sepolia → Base Sepolia)
- Hackathon faucet: check hackathon Discord/docs for sandbox ETH

---

## Key Contacts / Links

- Hackathon page: https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004
- ERC-8004 spec: https://eips.ethereum.org/EIPS/eip-8004
- Base Sepolia explorer: https://sepolia.basescan.org
- Hackathon Discord: check lablab.ai for invite
- Base Sepolia RPC: `https://sepolia.base.org`

---

## How to Use This Document

**After completing each phase task, update the Status column:**
- `⬜ TODO` → `🔄 IN PROGRESS` → `✅ DONE`

**Add notes** in the Notes column: transaction hashes, contract addresses, blockers, decisions made.

**Before starting any new phase:** Check that all prior phase tasks are ✅ DONE or explicitly deferred with a note. If tasks are deferred, carry them into the current phase's Codex prompt as priority work before new tasks.

This file is the single source of truth for what has been built and what remains. Every Codex session begins by reading this file.
