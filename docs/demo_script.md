# ChronoTrader — 3 Minute Demo Script

## 0:00–0:20 Intro
ChronoTrader is an autonomous ERC-8004 trading agent. It registers identity, executes signed trades, and writes reputation updates on-chain.

## 0:20–0:50 Prove identity
Run `python agent/main.py register` then show `agent/data/agent_card.json`.

## 0:50–1:45 Execute trade flow
Run `python agent/main.py trade` twice.
Show `agent/data/trades.json` and explain strategy → risk → execution.

## 1:45–2:20 Reputation update
Run `python agent/main.py validate`.
Show generated `agent/data/reputation_submission.json`.

## 2:20–2:45 Metrics and status
Run `python agent/main.py status`.
Highlight Sharpe, drawdown, and win rate.

## 2:45–3:00 Close
Summarize that every cycle creates auditable trade artifacts and normalized reputation scoring.
