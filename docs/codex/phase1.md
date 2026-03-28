# Codex Prompt — Phase 1: Foundation
**Days 1–3 | March 30 – April 1, 2026**  
**Goal:** Contracts compile, tests pass, deployed to Base Sepolia, agent registered on ERC-8004

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now.**

Check the Phase 1 table in `docs/onboarding.md`. For each task:
- If status is `✅ DONE` — skip it, do not re-implement it
- If status is `🔄 IN PROGRESS` or `⬜ TODO` — this is your work
- If anything from a previous session shows partial work (notes in the Notes column) — finish that first before starting fresh tasks

**Step 2 — Check the "What's next after Phase 1" line in `docs/onboarding.md`.**  
If you're resuming mid-phase, this tells you what the next phase expects. Do not leave Phase 1 with anything that would block Phase 2.

**Step 3 — Update `docs/onboarding.md` as you complete each task.** Change `⬜ TODO` → `✅ DONE` and add transaction hashes / contract addresses in the Notes column. Do this incrementally, not at the end.

---

## Context

You are working on **ChronoTrader**, an autonomous AI trading agent built for the ERC-8004 hackathon (Mar 30 – Apr 12, 2026). The project uses:
- **Foundry** for Solidity smart contracts (already written in `contracts/src/`)
- **CrewAI + GPT-4** for the Python agent (already written in `agent/`)
- **Base Sepolia** testnet (chain ID: 84532)
- **ERC-8004** Identity, Reputation, and Validation registries

The contracts are written but may have bugs, compilation errors, or missing pieces. The deployment script may be incomplete. Your job in Phase 1 is to get everything compiling, tested, and deployed.

---

## Goal

By the end of Phase 1, **all of the following must be true:**
1. `forge build` completes with zero errors
2. `forge test` passes all 3 test files (IdentityRegistry, RiskManager, TradeIntent)
3. All contracts deployed to Base Sepolia with addresses confirmed
4. `.env` updated with deployed contract addresses
5. Agent card JSON created and pinned to IPFS (or hosted publicly)
6. Agent registered on IdentityRegistry — Agent ID obtained
7. Registration verifiable on-chain (cast call confirms tokenURI)

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` before writing code.** Check every Phase 1 task status.
- [ ] Fix all compiler warnings and errors — `forge build` must exit 0 with no warnings
- [ ] All tests must PASS — no skipped tests, no commented-out assertions
- [ ] Use **Base Sepolia** (chain ID 84532, RPC: `https://sepolia.base.org`) for deployment — NOT mainnet, NOT Ethereum Sepolia
- [ ] Write deployed contract addresses to `.env` AND to the Phase 1 table in `docs/onboarding.md`
- [ ] The agent card JSON must be valid JSON matching the ERC-8004 spec format shown in `agent/main.py:create_agent_card()`
- [ ] After registration, verify with `cast call` that the agent ID exists and tokenURI is set
- [ ] Update `docs/onboarding.md` Phase 1 task table as each task completes (not at the end)

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** deploy to Ethereum mainnet or Ethereum Sepolia — Base Sepolia only
- [ ] **MUST NOT** skip tests or mark them as passing without running them
- [ ] **MUST NOT** hardcode private keys in any file (use `.env` only)
- [ ] **MUST NOT** commit `.env` to git (it's in `.gitignore` — verify this)
- [ ] **MUST NOT** leave `TODO` comments in contract code without adding them to `docs/onboarding.md` as deferred tasks
- [ ] **MUST NOT** use mock/stub addresses for registries — deploy real contracts

---

## Implementation Steps

### Step 1: Audit Contracts for Compilation Issues

```bash
cd contracts
forge build
```

For each error:
- Fix import paths if needed (`lib/` directory structure)
- Fix interface compliance (`IIdentityRegistry`, `IReputationRegistry`, `IValidationRegistry`)
- Ensure Solidity version compatibility across all files (check `foundry.toml` pragma)
- Fix any missing function implementations

Common issues to check:
- `StrategyVault.sol` and `RiskManager.sol` likely have TODO stubs — ensure they at least compile
- Interface functions must all be implemented
- Check that `TradeIntent.sol` correctly defines the EIP-712 domain separator with chain ID

### Step 2: Run and Fix Tests

```bash
cd contracts
forge test -vvv
```

Fix each failing test. The test files are:
- `test/IdentityRegistry.t.sol` — register(), tokenURI(), ownerOfAgent()
- `test/RiskManager.t.sol` — position size checks, daily loss limits, drawdown limits
- `test/TradeIntent.t.sol` — EIP-712 signing, nonce tracking, deadline enforcement

If a test is testing functionality that doesn't exist yet, implement the minimum contract logic needed to make the test pass. Do not delete or skip tests.

Add at least 2 additional test cases if you notice important edge cases not covered:
- IdentityRegistry: register from zero address should revert
- RiskManager: position at exactly max size should pass (boundary condition)
- TradeIntent: expired deadline should revert

### Step 3: Write and Run Deployment Script

Check `contracts/script/Deploy.s.sol`. Ensure it:
1. Deploys IdentityRegistry
2. Deploys ReputationRegistry
3. Deploys ValidationRegistry
4. Deploys TradeIntent (with correct chain ID for Base Sepolia: 84532)
5. Deploys RiskManager (with reference to TradeIntent)
6. Deploys StrategyVault (with reference to RiskManager)
7. Logs all addresses with `console.log`
8. Saves addresses to a JSON file at `contracts/deployed_addresses.json`

Deploy to Base Sepolia:
```bash
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.base.org \
  --broadcast \
  --private-key $AGENT_PRIVATE_KEY \
  --verify \
  --etherscan-api-key $BASESCAN_API_KEY

# If etherscan verification fails, skip it and verify manually later
```

After deployment, copy addresses to `.env`.

### Step 4: Create and Pin Agent Card

In `agent/data/agent_card.json`, generate the agent card. The format must match the ERC-8004 spec exactly:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "ChronoTrader",
  "description": "Autonomous AI trading agent with ERC-8004 trust. Executes momentum and mean-reversion strategies with verifiable on-chain performance.",
  "image": "",
  "services": [
    {
      "name": "A2A",
      "endpoint": "",
      "version": "0.3.0"
    }
  ],
  "x402Support": false,
  "active": true,
  "supportedTrust": ["reputation", "crypto-economic"],
  "capabilities": {
    "strategies": ["momentum", "mean_reversion", "yield_optimization"],
    "riskLimits": {
      "maxPositionSizePct": 20,
      "maxDailyLossPct": 5,
      "maxDrawdownPct": 15
    },
    "supportedAssets": ["ETH", "BTC", "USDC"],
    "supportedProtocols": ["uniswap-v3"]
  }
}
```

Pin to IPFS using one of:
- Pinata (free tier at pinata.cloud) — upload file, get `ipfs://Qm...` URI
- Web3.Storage — alternative
- If no IPFS access: host on GitHub raw (less ideal but acceptable for hackathon)

### Step 5: Register Agent On-Chain

```bash
# Set NETWORK=base_sepolia in .env first
python agent/main.py register
```

If the registration script fails:
1. Check `IDENTITY_REGISTRY_ADDRESS` is set in `.env`
2. Check wallet has Base Sepolia ETH (at least 0.01 ETH for gas)
3. Check `IPFS_GATEWAY` is set correctly
4. Run `init_tools()` is called before creating agents in `main.py`

After registration:
```bash
# Verify on-chain
cast call $IDENTITY_REGISTRY_ADDRESS \
  "agentCount()(uint256)" \
  --rpc-url https://sepolia.base.org

cast call $IDENTITY_REGISTRY_ADDRESS \
  "tokenURI(uint256)(string)" 1 \
  --rpc-url https://sepolia.base.org
```

The tokenURI should return the IPFS URI of the agent card.

### Step 6: Update `docs/onboarding.md`

For each completed task in the Phase 1 table:
- Change status to `✅ DONE`
- Add the contract address or tx hash in Notes column

Example:
```markdown
| Deploy to Base Sepolia | ✅ DONE | tx: 0xabc..., block: 12345678 |
| IDENTITY_REGISTRY_ADDRESS | ✅ DONE | 0x1234...5678 |
```

---

## Definition of Done

Phase 1 is complete when ALL of the following are true:

- [ ] `forge build` exits 0 with zero errors and zero warnings
- [ ] `forge test` exits 0 with all tests passing (output shows "Test result: ok")
- [ ] `contracts/deployed_addresses.json` exists with all 6 contract addresses
- [ ] `.env` has all contract address variables filled in
- [ ] `agent/data/agent_card.json` exists with valid ERC-8004 JSON
- [ ] Agent card is accessible via IPFS URI (can be fetched with `curl`)
- [ ] `python agent/main.py register` completes successfully
- [ ] Agent ID is set in `.env` as `AGENT_ID=1` (or whatever ID was assigned)
- [ ] `cast call` confirms registration: `tokenURI(1)` returns the IPFS URI
- [ ] All Phase 1 tasks in `docs/onboarding.md` show `✅ DONE`
- [ ] `docs/onboarding.md` Phase 1 "What's next" section confirms Phase 2 is unblocked

---

## Resources

- Base Sepolia RPC: `https://sepolia.base.org`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- Base Sepolia ETH Faucet: `https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet`
- ERC-8004 Spec: `https://eips.ethereum.org/EIPS/eip-8004`
- Foundry docs: `https://book.getfoundry.sh`
- Pinata (IPFS): `https://www.pinata.cloud`
- Hackathon page: `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
