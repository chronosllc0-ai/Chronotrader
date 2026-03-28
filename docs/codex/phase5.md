# Codex Prompt — Phase 5: Polish & Submit
**Days 12–14 | April 10–12, 2026**  
**Goal:** Submission-ready — clean README, Devpost page, demo video, live dashboard

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now.**

Open `docs/onboarding.md` and check:
1. **Phase 1 tasks** — all `✅ DONE`? All contract addresses must be final.
2. **Phase 2 tasks** — all `✅ DONE`? Trade pipeline must be working.
3. **Phase 3 tasks** — all `✅ DONE`? Loop and trade history must be running.
4. **Phase 4 tasks** — all `✅ DONE`? Reputation scores must be on-chain before you write the Devpost description.
5. **Phase 4 "What's next" line** — confirms Phase 5 is unblocked (dashboard, README, Devpost)
6. **Phase 5 task table** — check which tasks are already `✅ DONE` if resuming mid-phase
7. **Notes columns across all phases** — collect ALL contract addresses, tx hashes, Agent ID, subgraph URL (if deployed). You will need all of these for the README and Devpost.

**Step 2 — If any prior phase has incomplete tasks, finish them now.** Phase 5 requires:
- All contracts deployed (addresses in `.env` and `docs/onboarding.md`)
- At least one reputation score on-chain (for the demo)
- At least 10 trade cycles logged (for performance metrics to look meaningful)
- `python agent/main.py status` working (for live demo)

**Step 3 — The deadline is April 12, 2026. Work backwards from that deadline.** Allocate:
- Day 12 (April 10): README + `.env.example` + demo script
- Day 13 (April 11): Record demo video + Devpost draft
- Day 14 (April 12): Final review + submit to Devpost before midnight UTC

**Step 4 — Update `docs/onboarding.md` Phase 5 task table as you complete each task.**

---

## Context

Phase 4 gave you: reputation accumulating on-chain, validators scoring performance, the full ERC-8004 stack live.

Phase 5 is **the presentation layer** — making everything you've built legible and compelling to judges. The Devpost submission, README, and demo video are what judges experience before they look at the code. A project with great execution but a poor submission will score below its potential.

The demo video is the single most important artifact. Judges watch demos first. The 3-minute video must show the **complete user journey**: register agent → execute trade → reputation updates on-chain. Every step must be visible and understandable to a non-technical judge.

---

## Goal

By the end of Phase 5, **all of the following must be true:**
1. README.md reflects the final deployed state with all contract addresses on Base Sepolia
2. `docs/demo_script.md` written (3-minute video script, scene by scene)
3. Demo video recorded (Loom or OBS — 720p minimum) and link added to README and Devpost
4. Devpost submission text complete (600–900 words) covering Inspiration, What It Does, How We Built It, Challenges, What's Next
5. `.env.example` updated with all variable names (no values)
6. Project submitted to Devpost before April 12, 2026 midnight UTC
7. *(Optional)* Frontend dashboard deployed (Next.js or static HTML) showing reputation score and trade history

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` FIRST. Collect all contract addresses and tx hashes before writing anything.**
- [ ] README must have a "Deployed Contracts" section with all 6 contract addresses hyperlinked to `sepolia.basescan.org`
- [ ] README must have a "Demo" section with a link to the video and a link to the live Devpost page
- [ ] Demo script must be exactly 3 minutes — time yourself reading it aloud. Do not exceed 3 minutes.
- [ ] Demo video must show: (1) `cast call` proving agent is registered, (2) `python main.py trade` executing a live trade, (3) tx appearing on `sepolia.basescan.org`, (4) `python main.py validate` updating reputation, (5) reputation on-chain via `cast call`
- [ ] Devpost text must mention ERC-8004 by name and explain how the three registries are used
- [ ] `.env.example` must include ALL variables in the actual `.env` — no variable left out
- [ ] Submit to Devpost before April 12 deadline. Set a phone reminder.
- [ ] Update `docs/onboarding.md` Phase 5 task table as each task completes

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** submit to Devpost without a working demo video link — this is a dealbreaker for judges
- [ ] **MUST NOT** list placeholder contract addresses like `0x0000...` in the README — all addresses must be real and verified
- [ ] **MUST NOT** commit `.env` to the repo — verify `.gitignore` has `.env` before final push
- [ ] **MUST NOT** record the demo video in a cluttered terminal — use a clean shell, large font (18pt+), dark theme
- [ ] **MUST NOT** exceed 3 minutes in the demo video — judges watch many videos and will stop watching
- [ ] **MUST NOT** leave TODO comments or placeholder text in the README or Devpost submission

---

## Implementation Steps

### Step 1: Collect All Final Artifacts

Before writing anything, run this checklist script to collect all the information you need:

```bash
# Print all the info you'll need for README and Devpost
python -c "
import os, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

print('=== CONTRACT ADDRESSES ===')
print('IDENTITY_REGISTRY:', os.getenv('IDENTITY_REGISTRY_ADDRESS'))
print('REPUTATION_REGISTRY:', os.getenv('REPUTATION_REGISTRY_ADDRESS'))
print('VALIDATION_REGISTRY:', os.getenv('VALIDATION_REGISTRY_ADDRESS'))
print('RISK_ROUTER:', os.getenv('RISK_ROUTER_ADDRESS'))
print('SANDBOX_VAULT:', os.getenv('SANDBOX_VAULT_ADDRESS'))
print()
print('=== AGENT INFO ===')
print('AGENT_ID:', os.getenv('AGENT_ID'))
print('AGENT_WALLET:', os.getenv('AGENT_WALLET_ADDRESS', 'check .env'))
print()

perf = Path('agent/data/performance.json')
if perf.exists():
    m = json.loads(perf.read_text())
    print('=== PERFORMANCE ===')
    print('Total Trades:', m.get('total_trades'))
    print('Win Rate:', f\"{m.get('win_rate', 0):.1f}%\")
    print('Sharpe Ratio:', f\"{m.get('sharpe_ratio', 0):.3f}\")
    print('Max Drawdown:', f\"{m.get('max_drawdown_pct', 0):.2f}%\")
    print('Total PnL:', f\"\${m.get('total_pnl_usd', 0):.2f}\")

trades = Path('agent/data/trades.json')
if trades.exists():
    t = json.loads(trades.read_text())
    executed = [x for x in t if x.get('status') == 'EXECUTED']
    print()
    print('=== TRADE HISTORY ===')
    print(f'Total records: {len(t)}')
    print(f'Executed trades: {len(executed)}')
    if executed:
        print(f'First tx hash: {executed[0].get(\"tx_hash\")}')
        print(f'Last tx hash: {executed[-1].get(\"tx_hash\")}')
"
```

Save this output. You will reference it throughout Phase 5.

### Step 2: Update README.md

The README is the first thing judges see in the repo. It must be clean and complete.

Replace the existing README.md with a structured document that includes:

**Sections (in order):**
1. **Project title + one-sentence description** — "ChronoTrader is an autonomous AI trading agent with verifiable on-chain reputation, built on ERC-8004."
2. **Demo** — embedded video thumbnail or link, Devpost link
3. **What It Does** — 3–4 bullet points, plain language
4. **Architecture** — the 3-layer diagram (Solidity contracts → CrewAI agents → Chainlink feeds)
5. **Deployed Contracts** — table with all addresses linked to basescan
6. **Quickstart** — `git clone`, `pip install`, `cp .env.example .env`, `python main.py register`, `python main.py loop`
7. **Performance** — current Sharpe ratio, win rate, drawdown (update with real numbers before submission)
8. **Tech Stack** — table matching `docs/onboarding.md` tech stack section
9. **ERC-8004 Integration** — explain how Identity, Reputation, and Validation registries are used
10. **Hackathon** — ERC-8004 Hackathon Apr 2026, lablab.ai link

**Deployed Contracts section template:**
```markdown
## Deployed Contracts (Base Sepolia)

| Contract | Address | Explorer |
|----------|---------|---------|
| IdentityRegistry | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |
| ReputationRegistry | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |
| ValidationRegistry | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |
| TradeIntent | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |
| RiskManager | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |
| StrategyVault | `0x...` | [view](https://sepolia.basescan.org/address/0x...) |

**Agent ID:** 1 (registered on IdentityRegistry)  
**Network:** Base Sepolia (Chain ID: 84532)
```

### Step 3: Update `.env.example`

```bash
# ChronoTrader — Environment Variables
# Copy to .env and fill in your values

# LLM
OPENAI_API_KEY=

# Blockchain
AGENT_PRIVATE_KEY=
AGENT_WALLET_ADDRESS=
NETWORK=base_sepolia
RPC_URL=https://sepolia.base.org

# ERC-8004 Registries (deployed — use addresses from README)
IDENTITY_REGISTRY_ADDRESS=
REPUTATION_REGISTRY_ADDRESS=
VALIDATION_REGISTRY_ADDRESS=

# Trading
RISK_ROUTER_ADDRESS=
SANDBOX_VAULT_ADDRESS=
SANDBOX_RISK_ROUTER_ADDRESS=

# Agent Identity
AGENT_ID=
IPFS_GATEWAY=https://gateway.pinata.cloud/ipfs/
AGENT_CARD_IPFS_URI=

# Optional — Etherscan verification
BASESCAN_API_KEY=

# Optional — The Graph
SUBGRAPH_ENDPOINT=
```

### Step 4: Write `docs/demo_script.md`

```markdown
# ChronoTrader — 3-Minute Demo Script

**Total runtime: 3:00 | Target: 2:45 to leave buffer**

---

## Scene 1: Introduction (0:00–0:20)
*[Terminal visible, project root open]*

"ChronoTrader is an autonomous AI trading agent that earns verifiable on-chain reputation through actual performance. Every trade is signed with EIP-712. Every reputation score is computed from real metrics and stored on-chain via ERC-8004. No trust claims — just proof."

## Scene 2: Prove Agent Is Registered (0:20–0:50)
*[Run cast call to show agent exists on-chain]*

```bash
cast call $IDENTITY_REGISTRY_ADDRESS \
  "tokenURI(uint256)(string)" 1 \
  --rpc-url https://sepolia.base.org
```

"Agent ID 1 is registered on the IdentityRegistry on Base Sepolia. The tokenURI points to our agent card JSON on IPFS — this is the ERC-8004 identity."

*[Open the IPFS link in browser — show the agent card JSON]*

## Scene 3: Execute a Live Trade (0:50–1:45)
*[Run the trade command]*

```bash
NETWORK=base_sepolia python agent/main.py trade
```

"Watch as the 3-agent pipeline runs — Strategy Agent analyzes Chainlink price data, Risk Agent validates the position size against on-chain limits, Execution Agent signs the TradeIntent with EIP-712 and submits to the sandbox Risk Router."

*[Wait for output — point to key lines: APPROVED, tx hash, validation hash]*

"Transaction hash logged. Opening on Basescan..."

*[Open sepolia.basescan.org/tx/[hash]]*

"The trade is confirmed on Base Sepolia. This is a real on-chain transaction."

## Scene 4: Update Reputation (1:45–2:20)
*[Run the validator]*

```bash
python agent/main.py validate
```

"The validation agent computes a reputation score from real metrics — Sharpe ratio, win rate, drawdown control — and submits it to the ReputationRegistry. Let's verify it on-chain..."

```bash
cast call $REPUTATION_REGISTRY_ADDRESS \
  "getReputation(uint256)(uint256)" 1 \
  --rpc-url https://sepolia.base.org
```

"Score is now live on-chain. Any validator, any dApp, any counterparty can read this score. That's the ERC-8004 trust primitive."

## Scene 5: Performance Summary (2:20–2:50)
*[Run status command]*

```bash
python agent/main.py status
```

*[Show Rich terminal table with Sharpe, win rate, drawdown, PnL, strategy comparison]*

"Everything is auditable — trade history on disk, validation artifacts on-chain, reputation scoring live. ChronoTrader doesn't just claim to be a trustworthy agent. It proves it."

## Scene 6: Close (2:50–3:00)
"Built for the ERC-8004 Hackathon, April 2026. All code open source at github.com/chronosllc0-ai/Chronotrader."
```

### Step 5: Record the Demo Video

**Setup checklist before recording:**
- [ ] Terminal font size: 18pt minimum
- [ ] Dark theme (VS Code Dark+, Dracula, or similar)
- [ ] Window maximized — no distracting icons or notifications
- [ ] `.env` is loaded and all env vars are set
- [ ] `python agent/main.py status` works cleanly before you start recording
- [ ] Browser tab open at `sepolia.basescan.org` — ready to paste tx hash
- [ ] Phone on silent

**Recording tools:**
- [Loom](https://loom.com) (easiest — record screen + narration, instant shareable link)
- OBS Studio (more control, export as MP4 then upload to YouTube/Loom)
- QuickTime (Mac) + upload to YouTube

**After recording:**
- Trim any dead air at start/end
- Add the video link to README.md "Demo" section
- Add the video link to Devpost submission

### Step 6: Write and Submit Devpost

Use the Devpost draft below as your starting template. Edit with real numbers, real tx hashes, and any unique aspects of your implementation before submitting.

---

**📋 DEVPOST SUBMISSION DRAFT — Edit Before Submitting**

---

**Project Name:** ChronoTrader

**Tagline:** Autonomous AI trading agent with verifiable on-chain reputation — powered by ERC-8004.

---

### Inspiration

The DeFi ecosystem has no shortage of automated trading agents. What it lacks is a way to trust them. How do you know an agent's claimed 40% APY is real? How do you know it won't blow up your capital next week? Today, you can't — you either trust the team's word or you don't participate.

ERC-8004 changes that. It gives AI agents a trust layer that's native to the blockchain: cryptographic identity, verifiable performance history, and on-chain reputation accumulated through actual behavior. We built ChronoTrader to prove out that vision — an agent that doesn't just claim to be trustworthy, but proves it through every signed trade and every on-chain reputation update.

---

### What It Does

ChronoTrader is a fully autonomous AI trading agent that:

1. **Registers its identity on-chain** via ERC-8004's IdentityRegistry, with a structured agent card (strategies, risk limits, capabilities) pinned to IPFS and referenced by tokenURI
2. **Executes DeFi trades** on Base Sepolia using EIP-712 signed TradeIntents, routed through the Hackathon Capital sandbox Risk Router — every trade is a verifiable on-chain transaction
3. **Accumulates verifiable reputation** by computing performance metrics (Sharpe ratio, win rate, max drawdown) after each trading session and submitting scores to ERC-8004's ReputationRegistry
4. **Submits validation artifacts** after every trade cycle — hashing the full cycle data and storing it on-chain via the ValidationRegistry, creating an immutable audit trail
5. **Runs continuously** with a 15-minute trading loop, alternating between momentum and mean-reversion strategies to build a multi-strategy performance record

The result: any counterparty can query the on-chain registries and get a cryptographically verifiable picture of the agent's performance history. No trust required.

---

### How We Built It

**Smart Contracts (Solidity + Foundry)**

We deployed six contracts to Base Sepolia: the three ERC-8004 registries (Identity, Reputation, Validation), plus TradeIntent (EIP-712 typed data structure), RiskManager (on-chain position limits enforced per trade), and StrategyVault (capital tracking).

The RiskManager enforces hard limits on-chain: maximum 20% position size, maximum 5% daily loss, maximum 15% drawdown. These limits are checked at the contract level before any trade executes — the agent cannot bypass them.

**AI Agent Framework (CrewAI + GPT-4)**

The Python agent uses a 3-agent CrewAI pipeline:
- **Strategy Agent** — analyzes live Chainlink ETH/USD and BTC/USD price data and generates a structured JSON trade signal (BUY/SELL/HOLD, position size, rationale)
- **Risk Agent** — validates the signal against on-chain RiskManager limits and current portfolio state
- **Execution Agent** — builds a TradeIntent struct, signs it with EIP-712, submits to the sandbox Risk Router, and records the validation artifact

All three agents run sequentially per trade cycle using CrewAI's sequential process.

**EIP-712 Signing Pipeline**

The EIP-712 signing pipeline was the most technically demanding piece. The domain separator in `eip712_signer.py` must match the one in `RiskManager.sol` exactly — same name, version, chain ID (84532), and verifying contract address. We built a `cast call` verification step into the Phase 2 flow to confirm the signature is accepted on-chain.

**Performance & Reputation**

`metrics.py` tracks per-trade returns, computes a rolling Sharpe ratio (annualized for 15-minute cycles), win rate, and max drawdown. The `validation_agent.py` translates these into a 0–10000 basis point reputation score and submits it to ReputationRegistry after each trading session.

**Infrastructure**

- Base Sepolia testnet (chain ID 84532) for all on-chain operations
- Chainlink price feeds for live ETH/USD and BTC/USD data
- IPFS (Pinata) for agent card metadata
- Rich library for terminal dashboards
- JSON + CSV dual-format trade logging for full auditability

---

### Challenges We Ran Into

**EIP-712 Domain Separator Alignment** — Getting the off-chain signing to produce signatures the on-chain RiskManager accepts took significant debugging. The domain separator fields must match byte-for-byte, including the chain ID being read dynamically (not hardcoded) to avoid mismatch on redeployment.

**Nonce Management Under Load** — The continuous trading loop exposed a subtle issue: using `eth_getTransactionCount` with `pending` status during network congestion returns incorrect nonces. We built a `NonceManager` class that maintains local nonce state and only re-syncs from the chain after a confirmed nonce conflict error.

**Reputation Score Normalization** — The Sharpe ratio can be negative (during drawdown periods) or unbounded upward. We had to design a normalization function that maps real-world Sharpe values to the 0–10000 basis point range in a way that doesn't produce extreme placeholder-looking scores.

**Strategy Output Reliability** — GPT-4 doesn't always produce clean JSON on the first try. We added explicit JSON-only prompting constraints and a strict parser that retries the analysis task if output is invalid — the risk pipeline never sees malformed data.

---

### What's Next

**zkML integration** — The strategy execution is currently transparent (anyone can see which signals GPT-4 generated). With zkML (e.g., EZKL), we could prove the strategy was run correctly without revealing the strategy logic — enabling strategy confidentiality while maintaining verifiability.

**Full TEE attestation** — We implemented an attestation stub using Phala Network's data structure. Full integration would run the entire strategy engine inside a Trusted Execution Environment, making the computation itself tamper-proof and remotely attestable.

**Multi-agent competition** — ERC-8004 reputation enables agent-vs-agent comparison natively. A leaderboard built on The Graph subgraph data could let users pick the highest-reputation strategy agent for their capital allocation — a fully decentralized agent marketplace.

**Live capital integration** — Connecting to production Uniswap V3 on Base mainnet (with real capital caps) would validate performance under real market conditions. The ERC-8004 reputation accumulated on testnet provides the track record needed to bootstrap trust for a live deployment.

---

### Tech Stack

Solidity · Foundry · CrewAI · GPT-4 · Python · web3.py · EIP-712 · Base Sepolia · Chainlink · IPFS · Pinata · Rich · ERC-8004

---

**Built at the ERC-8004 AI Trading Agents Hackathon | March–April 2026**  
**GitHub:** https://github.com/chronosllc0-ai/Chronotrader

---

*[END OF DEVPOST DRAFT — Replace bracketed placeholders with real data before submitting]*

---

### Step 7: Optional Frontend Dashboard

If time permits (6+ hours remaining before deadline), build a minimal Next.js dashboard:

```bash
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install wagmi viem @tanstack/react-query
```

Key pages:
- `/` — Agent card, registration status, current reputation score (read from ReputationRegistry via wagmi)
- `/trades` — Trade history table from a static JSON endpoint or The Graph query
- `/performance` — Sharpe, win rate, drawdown charts (use recharts)

Deploy to Vercel:
```bash
npx vercel --prod
```

Add the dashboard URL to README.md "Demo" section.

**If less than 6 hours remain — skip the frontend.** A polished README + demo video + Devpost submission is worth more than a buggy dashboard.

### Step 8: Final Pre-Submission Checklist

Run these checks in order before hitting Submit on Devpost:

```bash
# 1. Verify .env is not committed
git log --oneline --all -- .env
# Should return nothing

# 2. Verify .gitignore has .env
grep "^\.env$" .gitignore
# Should return .env

# 3. Verify forge build still passes (contracts haven't drifted)
cd contracts && forge build && forge test

# 4. Verify trade command still works
NETWORK=base_sepolia python agent/main.py trade

# 5. Verify validate command still works
python agent/main.py validate

# 6. Verify status command shows all metrics
python agent/main.py status

# 7. Verify all contract addresses in README match .env
# Read README "Deployed Contracts" section and compare to .env values manually

# 8. Verify demo video link works (not broken, not private)
# Open the link in an incognito window

# 9. Final push
git add -A
git commit -m "chore: final pre-submission cleanup"
git push origin main
```

Only after all checks pass: submit on Devpost.

### Step 9: Update `docs/onboarding.md`

```markdown
| Submitted to Devpost before Apr 12 deadline | ✅ DONE | Devpost URL: https://devpost.com/... |
```

---

## Definition of Done

Phase 5 is complete when ALL of the following are true:

- [ ] All Phase 1, 2, 3, and 4 tasks in `docs/onboarding.md` are `✅ DONE`
- [ ] README.md has "Deployed Contracts" section with all 6 real addresses linked to basescan
- [ ] README.md has "Demo" section with working video link
- [ ] `docs/demo_script.md` exists and is timed at ≤3 minutes
- [ ] Demo video is recorded, uploaded, and link is working in an incognito window
- [ ] `.env.example` has all variable names (no values) and is committed to repo
- [ ] `.env` is NOT in the repo (verified with `git log --all -- .env`)
- [ ] Devpost submission text is complete (600–900 words, all sections filled)
- [ ] Devpost submission is published (not just saved as draft)
- [ ] Devpost submission URL added to `docs/onboarding.md` Phase 5 Notes
- [ ] Project submitted to Devpost before April 12, 2026 midnight UTC
- [ ] All Phase 5 tasks in `docs/onboarding.md` show `✅ DONE`

---

## Resources

- Devpost submission: `https://devpost.com` — log in and find the ERC-8004 hackathon
- Loom (screen recording): `https://loom.com`
- Vercel (frontend deploy): `https://vercel.com`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- Hackathon page: `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
- ERC-8004 spec: `https://eips.ethereum.org/EIPS/eip-8004`
- Deadline: **April 12, 2026 — do not miss this**
