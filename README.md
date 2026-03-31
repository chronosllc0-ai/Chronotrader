# ChronoTrader

Autonomous AI trading agent with ERC-8004 trust and verifiable reputation.

## Demo
- Demo script: `docs/demo_script.md`
- CLI flow: `python agent/main.py register && python agent/main.py trade && python agent/main.py validate && python agent/main.py status`

## What It Does
- Registers an ERC-8004 compatible agent card.
- Runs strategy → risk → execution trade cycles.
- Writes trade artifacts to JSON/CSV and computes Sharpe/win-rate/drawdown.
- Computes normalized reputation score (0–9999 bps) and prepares on-chain submission payload.

## Architecture
- Solidity registries + trading contracts in `contracts/`
- Python agent runtime in `agent/`
- Operational docs and phase prompts in `docs/`

## Deployed Contracts (Base Sepolia)
Fill in after broadcast deployment:

| Contract | Address |
|---|---|
| IdentityRegistry | `TBD` |
| ReputationRegistry | `TBD` |
| ValidationRegistry | `TBD` |
| TradeIntent | `TBD` |
| RiskManager | `TBD` |
| StrategyVault | `TBD` |

## Quickstart
```bash
cp .env.example .env
pip install -r agent/requirements.txt
cd contracts && forge build && forge test
cd .. && python agent/main.py register
python agent/main.py trade
python agent/main.py validate
python agent/main.py status
```

## ERC-8004 Integration
- Identity: `IdentityRegistry.register(uri)` stores agent card URI.
- Validation: each cycle includes a deterministic validation hash.
- Reputation: score is computed from observed metrics, then mapped for contract submission.

## Hackathon
Built for AI Trading Agents with ERC-8004 (March–April 2026).
