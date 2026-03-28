# Codex Prompt — Phase 5: Polish & Submit
**Days 12–14 | April 10–12, 2026**  
**Goal:** Submission-ready — clean README with all contract addresses, Devpost text, demo video script, final performance report

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now. This is the most critical check of the entire sprint.**

Open `docs/onboarding.md` and verify **every single task across all 4 phases:**

**Phase 1 — Foundation:**
- [ ] All contracts deployed to Base Sepolia?
- [ ] Contract addresses in `.env` AND `docs/onboarding.md` Notes?
- [ ] Agent registered on IdentityRegistry?
- [ ] Agent ID confirmed on-chain?

**Phase 2 — Trading Core:**
- [ ] EIP-712 signing verified working?
- [ ] Risk Router integration working?
- [ ] At least one successful trade with tx hash?
- [ ] `performance.json` exists with real data?

**Phase 3 — Live Execution:**
- [ ] Loop ran 24+ hours without crashing?
- [ ] 50+ trade cycle entries in `trade_log.jsonl`?
- [ ] Circuit breakers tested?
- [ ] ValidationRegistry has 50+ artifacts?

**Phase 4 — Trust & Reputation:**
- [ ] Reputation score submitted to ReputationRegistry?
- [ ] On-chain reputation score > 0?
- [ ] Validator verification rate > 90%?
- [ ] (Bonus) Subgraph deployed?
- [ ] (Bonus) TEE attestation?

**Step 2 — For EVERY incomplete task you find, fix it before Phase 5 work.** Phase 5 is the showcase — you can only showcase what was built. Judges will click on Basescan links, query your subgraph, and check your contracts. Unverified claims hurt more than no claims.

**Step 3 — Phase 5 has no "MUST implement X" features.** It's about presenting what you built honestly and compellingly.

---

## Context

Phase 4 gave you: reputation scores on-chain, a running trading agent with a track record, validated trade artifacts.

Phase 5 is **the submission package** — making sure everything you built is visible, understandable, and impressive to judges who will spend 5–10 minutes evaluating your project.

The typical hackathon evaluation flow:
1. Judge reads README (60 seconds)
2. Judge watches demo video (3 minutes)
3. Judge opens Basescan, checks contract addresses, sees transactions
4. Judge reads Devpost description
5. Judge gives bonus points for: subgraph query working, TEE, unique strategy

Your job: make those 10 minutes count.

---

## Goal

By the end of Phase 5, **all of the following must be true:**
1. `README.md` updated with all deployed contract addresses, verified tx links, and actual performance metrics
2. Devpost submission page complete with full description, video link, GitHub link, contract addresses
3. 3-minute demo video recorded showing: identity registration → trading cycle → reputation accumulation
4. `docs/demo_script.md` written with exact narration script for demo
5. Final performance report generated from real data in `performance.json`
6. All contract addresses verified on Basescan
7. Submitted to Devpost before April 12 deadline

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` FIRST. Go through EVERY phase and fix every incomplete task before any Phase 5 work.**
- [ ] All contract addresses in README must be clickable Basescan links (not just hex strings)
- [ ] Performance metrics in README must come from real `performance.json` data — do not make up numbers
- [ ] Demo video must show the actual running system (not slides, not mockups)
- [ ] Devpost submission must include the GitHub link, contract addresses, and demo video
- [ ] Every `TODO` comment still in the code must be either implemented or removed before submission
- [ ] `.env.example` must have all variables documented with descriptions
- [ ] `AGENT_PRIVATE_KEY` must NOT appear in any committed file — double-check with `git grep AGENT_PRIVATE_KEY`
- [ ] Update `docs/onboarding.md` Phase 5 task table as each task completes

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** start Phase 5 work while Phase 1, 2, 3, or 4 has incomplete critical tasks
- [ ] **MUST NOT** put fake or estimated performance numbers in the README — use real data only
- [ ] **MUST NOT** submit with contract addresses that return 404 on Basescan
- [ ] **MUST NOT** show slides in the demo video as the main content — show the actual terminal/frontend
- [ ] **MUST NOT** leave `TODO: Set actual address` or similar placeholders in README
- [ ] **MUST NOT** upload `.env` to the repo — verify `.gitignore` covers it
- [ ] **MUST NOT** submit before reading the Devpost requirements for the specific hackathon

---

## Implementation Steps

### Step 1: Fix Every Open TODO

Search the entire codebase for remaining TODOs:
```bash
grep -rn "TODO" --include="*.py" --include="*.sol" --include="*.md" .
```

For each TODO found:
- If it's a feature that was supposed to be in Phases 1–4: implement it now if small (<30 min), or mark it as deferred in README ("Future Work")
- If it's a code comment explaining a future enhancement: convert to a GitHub Issue and remove from code
- The demo version must have zero critical-path TODOs

### Step 2: Update README.md

Replace the placeholder table in README with real data:

```markdown
## Deployed Contracts (Base Sepolia — Chain ID 84532)

| Contract | Address | Basescan |
|----------|---------|----------|
| IdentityRegistry | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |
| ReputationRegistry | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |
| ValidationRegistry | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |
| TradeIntent | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |
| RiskManager | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |
| StrategyVault | `0x...` | [View](https://sepolia.basescan.org/address/0x...) |

## Agent Registration
- **Agent ID:** 1
- **Registration TX:** [0x...](https://sepolia.basescan.org/tx/0x...)
- **Agent Card (IPFS):** [ipfs://Qm...](https://ipfs.io/ipfs/Qm...)

## Live Performance (as of April 10, 2026)

| Metric | Value |
|--------|-------|
| Total Trades | [REAL NUMBER from performance.json] |
| Win Rate | [REAL %] |
| Total PnL | $[REAL USD] |
| Sharpe Ratio | [REAL VALUE] |
| Max Drawdown | [REAL %] |
| Reputation Score | [REAL 0–100] / 100 |
| Validation Artifacts | [COUNT] |

*All metrics computed from on-chain data and `agent/data/performance.json`.*
```

Also update the Hackathon Compliance table with actual status (not just ✅ placeholders):

```markdown
## Hackathon Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ERC-8004 Identity Registry | ✅ | Agent #1 registered, [tx](https://sepolia.basescan.org/tx/0x...) |
| Reputation accumulation | ✅ | Score: X/100, [contract](https://sepolia.basescan.org/address/0x...) |
| Validation artifacts | ✅ | N artifacts, [registry](https://sepolia.basescan.org/address/0x...) |
| Hackathon Capital Sandbox | ✅ | [trades on Basescan](https://sepolia.basescan.org/address/WALLET) |
| EIP-712 TradeIntents | ✅ | All intents signed, [example tx](https://sepolia.basescan.org/tx/0x...) |
| Risk-adjusted profitability | ✅ | Sharpe: X.XX, Max DD: X.X% |
| The Graph subgraph | ✅/❌ | [GraphQL endpoint](https://...) or N/A |
| TEE attestation | ✅/❌ | [Attestation hashes in logs] or N/A |
```

### Step 3: Write `docs/demo_script.md`

Write the exact narration script for the 3-minute demo video:

```markdown
# ChronoTrader Demo Script — 3 Minutes

## [0:00 – 0:20] Hook and Overview (screen: README)
"ChronoTrader is an autonomous AI trading agent that earns reputation through verifiable on-chain performance. 
Built on ERC-8004 for the Base Sepolia hackathon. Let me show you what it does."

## [0:20 – 0:50] Identity Registration (screen: terminal + Basescan)
"First, the agent registers its identity on ERC-8004. One command:"
> Show: `python agent/main.py register`
> Show: Registration tx on Basescan
> Show: `tokenURI()` returning the IPFS agent card

"The agent card defines its capabilities — strategies it runs, risk limits, supported assets. 
Verifiable. Immutable. On-chain."

## [0:50 – 1:40] Trading Cycle (screen: terminal, Strategy → Risk → Execution)
"Now, a trading cycle. Three AI agents, three distinct roles:"
> Show: `python agent/main.py trade`
> Narrate as each phase runs:
  - Strategy Agent: "Analyzing ETH price on Chainlink. Sees bullish momentum. Recommends BUY at [price]."
  - Risk Agent: "Validating position size. Checking drawdown limits. Approves at 10% position."
  - Execution Agent: "Building EIP-712 signed TradeIntent. Submitting to Risk Router."
> Show: tx hash appearing on Basescan
> Show: swap in/out amounts

"Every step is logged. Every decision has a hash. Every trade is auditable."

## [1:40 – 2:10] Validation and Reputation (screen: terminal metrics table + Basescan)
"After execution, the cycle is hashed and submitted to ValidationRegistry."
> Show: validation artifact hash
> Show: `python agent/main.py reputation`
> Show: reputation score calculation: "Sharpe XX, win rate XX%, drawdown XX% → score: XX/100"
> Show: reputation submission tx on Basescan
> Show: `cast call` returning the on-chain reputation score

## [2:10 – 2:40] Performance Dashboard (screen: performance table or frontend if built)
"After [N] trading cycles over [X] days:"
> Show: rich performance table with real numbers
> "Sharpe ratio: [X]. Max drawdown: [X]%. Win rate: [X]%. [N] validation artifacts on-chain."
> If subgraph: show GraphQL query returning agent data

## [2:40 – 3:00] Closing
"ChronoTrader demonstrates that AI trading agents don't have to be black boxes.
ERC-8004 gives them identity, reputation, and accountability. 
Everything you just saw is on Base Sepolia. Links in the Devpost description."

---
# Technical Demo Fallback (if live demo has issues)
Pre-record terminal sessions using `asciinema`:
```bash
asciinema rec demo_registration.cast
asciinema rec demo_trading.cast
asciinema play demo_trading.cast
```
```

### Step 4: Generate Final Performance Report

Create a script that generates a markdown performance report from real data:

```python
# scripts/generate_report.py

import json
from pathlib import Path
from datetime import datetime

def generate_report():
    metrics_file = Path("agent/data/performance.json")
    log_file = Path("agent/data/trade_log.jsonl")
    
    if not metrics_file.exists():
        print("ERROR: performance.json not found. Run the agent first.")
        return
    
    metrics = json.loads(metrics_file.read_text())
    
    logs = []
    if log_file.exists():
        logs = [json.loads(line) for line in log_file.read_text().strip().split("\n") if line]
    
    # Count by outcome
    executed = sum(1 for l in logs if l.get("outcome") == "executed")
    rejected = sum(1 for l in logs if l.get("outcome") == "rejected")
    
    report = f"""# ChronoTrader Performance Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Summary

| Metric | Value |
|--------|-------|
| Total Cycles | {len(logs)} |
| Trades Executed | {executed} |
| Trades Rejected by Risk | {rejected} |
| Win Rate | {metrics.get('win_rate', 0):.1f}% |
| Total PnL | ${metrics.get('total_pnl_usd', 0):.2f} |
| Sharpe Ratio | {metrics.get('sharpe_ratio', 0):.4f} |
| Max Drawdown | {metrics.get('max_drawdown_pct', 0):.2f}% |
| Reputation Score | {metrics.get('reputation_score', 'Pending')} / 100 |

## Risk Controls Applied
- {rejected} trades blocked by Risk Agent ({rejected/len(logs)*100:.1f}% rejection rate)
- Daily loss limit triggered: [N times — check trade_log.jsonl for "circuit breaker" entries]
- Consecutive rejection pauses: [N times]

## On-Chain Evidence
- Validation artifacts in ValidationRegistry: {len(logs)}
- Reputation submissions: [N — check basescan]
- Agent registration: Block [BLOCK_NUMBER] on Base Sepolia

## Strategy Breakdown
[Add momentum vs mean_reversion comparison from performance_by_strategy.json if Phase 4 Step 4 was done]
"""
    
    report_path = Path("docs/performance_report.md")
    report_path.write_text(report)
    print(f"Report written to {report_path}")
    print(report)

if __name__ == "__main__":
    generate_report()
```

### Step 5: Write Devpost Submission Text

Write `docs/devpost_submission.md` with the complete Devpost description:

```markdown
# ChronoTrader — Devpost Submission

## What it does
ChronoTrader is an autonomous AI trading agent that uses ERC-8004's on-chain trust layer 
to register identity, execute DeFi strategies with EIP-712 signed TradeIntents, and build 
verifiable on-chain reputation through actual performance.

Three AI agents (CrewAI + GPT-4) form a trading desk: a strategist who reads Chainlink 
market data, a risk officer who enforces drawdown limits on-chain, and an execution 
specialist who signs and submits trades to the Hackathon Capital Risk Router.

Every trade cycle produces a cryptographic artifact. Every reputation point is earned.

## How we built it
- **Smart contracts:** Solidity + Foundry — ERC-8004 Identity/Reputation/Validation registries, 
  custom RiskManager with on-chain drawdown enforcement, EIP-712 TradeIntent struct
- **AI agents:** CrewAI + OpenAI GPT-4 — 3-agent pipeline with strict role separation, 
  deterministic risk checks (temp=0.0), probabilistic strategy analysis (temp=0.1)
- **Tools:** Chainlink price feeds (Base Sepolia), web3.py for EIP-712 signing, custom 
  metrics tracking (Sharpe ratio, max drawdown, win rate)
- **Network:** Base Sepolia — deployed and live for 14 days

## Challenges we ran into
[List 2–3 real challenges from your sprint — nonce management, EIP-712 alignment, etc.]

## Accomplishments
- [N] validation artifacts on-chain over 14 days
- Sharpe ratio: [REAL VALUE]
- Max drawdown held under 15% throughout
- On-chain reputation score: [REAL VALUE]/100

## What's next
- zkML proof of strategy computation
- Multi-agent composability — ChronoTrader as a service for other ERC-8004 agents
- Production deployment on Base mainnet

## Built With
crewai, python, solidity, foundry, openai, base-sepolia, erc-8004, eip-712, chainlink, web3py

## Try It Out
- GitHub: https://github.com/chronosllc0-ai/Chronotrader
- Demo video: [YouTube/Loom link]
- Base Sepolia contracts: [Basescan link]
```

### Step 6: Pre-Submission Checklist

Run through this before hitting Submit on Devpost:

```bash
# 1. No secrets in git
git grep "PRIVATE_KEY" --include="*.py" --include="*.sol" --include="*.md" --include="*.json"
git grep "sk-" --include="*.py"  # OpenAI keys

# 2. All contract addresses are real
grep -r "0x000000" contracts/  # Should be empty

# 3. README contract table is filled
grep "TODO" README.md  # Should be empty

# 4. Tests still pass
cd contracts && forge test -vvv

# 5. Agent runs fresh from clone
git clone . /tmp/chronotrader_test && cd /tmp/chronotrader_test
# Follow README quickstart and verify it works

# 6. IPFS agent card is accessible
curl https://ipfs.io/ipfs/[YOUR_HASH]/agent_card.json

# 7. Basescan links work
# Open each link from README in browser

# 8. Video link works (play it in incognito)
```

### Step 7: Submit

1. Go to the hackathon Devpost page at `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
2. Fill in all required fields using `docs/devpost_submission.md`
3. Upload or link demo video
4. Submit the GitHub repository link
5. Add all contract addresses
6. Submit before the April 12, 2026 deadline (check exact time)

After submitting:
- Update `docs/onboarding.md` Phase 5 "Submitted to Devpost" task to `✅ DONE`
- Add the Devpost submission URL to `docs/onboarding.md` Notes

---

## Definition of Done

Phase 5 (and the entire sprint) is complete when ALL of the following are true:

- [ ] All Phases 1–4 tasks in `docs/onboarding.md` are `✅ DONE` (or explicitly deferred with reason)
- [ ] `README.md` has all real contract addresses as clickable Basescan links
- [ ] `README.md` performance table has real numbers from `performance.json`
- [ ] `README.md` compliance table has real evidence links (not just ✅)
- [ ] `docs/demo_script.md` written and demo video recorded
- [ ] Demo video is publicly accessible (YouTube, Loom, or similar)
- [ ] `docs/devpost_submission.md` written with all sections complete
- [ ] `docs/performance_report.md` generated from real data
- [ ] `git grep PRIVATE_KEY` returns no results
- [ ] `forge test` still passes after all Phase 5 changes
- [ ] Devpost submission is complete and live before April 12 deadline
- [ ] All Phase 5 tasks in `docs/onboarding.md` show `✅ DONE`

---

## Devpost Deadline

**April 12, 2026** — check exact submission cutoff time on the hackathon page.  
Submit early. Do not wait until the last hour.

---

## Resources

- Hackathon Devpost: `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- asciinema (terminal recording): `https://asciinema.org`
- Loom (video recording): `https://loom.com`
- IPFS public gateway check: `https://ipfs.io/ipfs/[your_hash]`
