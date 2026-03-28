# Codex Prompt — Phase 3: Live Execution
**Days 7–9 | April 5–7, 2026**  
**Goal:** Agent executing real trades on Hackathon Capital Sandbox, emitting validation artifacts, continuous loop running

---

## ⚠️ BEFORE YOU WRITE A SINGLE LINE OF CODE

**Step 1 — Read `docs/onboarding.md` now.**

Open `docs/onboarding.md` and check:
1. **Phase 1 tasks** — are all statuses `✅ DONE`? If any are `⬜ TODO` or `🔄 IN PROGRESS`, **finish those first**. Phase 3 requires deployed contracts and a registered agent.
2. **Phase 2 tasks** — are all statuses `✅ DONE`? If any are incomplete, **finish Phase 2 first**. Phase 3 requires a working trade cycle (`python main.py trade` must run cleanly).
3. **Phase 2 "What's next" line** — confirms Phase 3 is unblocked (live execution, validation artifacts, continuous loop)
4. **Phase 3 task table** — check which tasks are already `✅ DONE` if resuming mid-phase
5. **Notes columns in Phase 1 & 2** — get contract addresses, Agent ID, sandbox addresses, and the first tx hash if already generated

**Step 2 — If Phase 1 or Phase 2 has incomplete tasks, finish them before proceeding.** Do not start Phase 3 work with a broken trade pipeline. Specifically:
- You NEED `python main.py trade` to work end-to-end (Phase 2 outcome)
- You NEED `SANDBOX_VAULT_ADDRESS` and `SANDBOX_RISK_ROUTER_ADDRESS` in `.env`
- You NEED `AGENT_ID` set in `.env`
- You NEED Chainlink feeds returning live prices (Phase 2 outcome)

**Step 3 — Update `docs/onboarding.md` Phase 3 task table as you complete each task.** Change `⬜ TODO` → `✅ DONE` and add tx hashes and loop cycle counts in the Notes column. Do this incrementally, not at the end.

---

## Context

Phase 2 gave you: a working trade cycle — strategy signal → risk check → EIP-712 signed intent → sandbox submission. One trade works. 

Phase 3 is **real execution at scale** — the continuous trading loop that runs every 15 minutes, accumulates trade history, computes live performance metrics from Chainlink price feeds, and handles failures gracefully. By the end of Phase 3, the agent should be able to run unattended overnight and produce a meaningful performance record.

The most critical piece: **the continuous loop must be error-resilient.** A single failed RPC call or gas estimation error must not crash the loop. Nonce tracking must be reliable. Every cycle, even failed ones, must produce a validation artifact.

---

## Goal

By the end of Phase 3, **all of the following must be true:**
1. At least one live trade executed on Base Sepolia sandbox with tx hash logged to disk
2. Validation artifacts submitted to ValidationRegistry after every trade cycle (success or failure)
3. `python agent/main.py loop` runs continuously with 15-minute cycles and recovers from errors
4. Trade history written to `agent/data/trades.json` AND `agent/data/trades.csv` after every cycle
5. Performance metrics (PnL, Sharpe, max drawdown) computed and current after every cycle
6. Chainlink ETH/USD and BTC/USD feeds actively used for price data (not mocked or hardcoded)
7. Error handling covers: failed RPC calls, gas estimation failures, nonce conflicts, tx reverts

---

## MUST DO — Hard Requirements

- [ ] **Read `docs/onboarding.md` FIRST. Finish all incomplete Phase 1 and Phase 2 tasks before starting Phase 3.**
- [ ] Every trade cycle (success or failure) must record a validation artifact hash to ValidationRegistry
- [ ] The trading loop (`python main.py loop`) must catch ALL exceptions at the cycle level — a single bad cycle must never stop the loop
- [ ] Nonce management must be explicit: track the last used nonce and increment, do not rely on pending tx count which can be wrong during congestion
- [ ] Gas escalation: on tx failure, retry with 20% higher gas price, up to 3 retries
- [ ] Chainlink feeds must be live — do NOT mock price data in Phase 3. If a feed call fails, retry 3 times then skip the cycle (log the skip)
- [ ] Trade history must be dual-format: JSON (full detail) and CSV (tabular, for easy inspection)
- [ ] After each loop cycle, print a Rich status line to terminal: cycle number, last action, PnL so far, next cycle in Xs
- [ ] Update `docs/onboarding.md` Phase 3 task table as each task completes

## MUST NOT DO — Hard Prohibitions

- [ ] **MUST NOT** start Phase 3 work if Phase 2 has incomplete tasks — finish Phase 2 first
- [ ] **MUST NOT** use `time.sleep()` for the loop timer without catching `KeyboardInterrupt` gracefully (Ctrl+C must exit cleanly and save state)
- [ ] **MUST NOT** mock Chainlink prices — all price data must come from live on-chain feeds
- [ ] **MUST NOT** let the loop run without saving trade history after every cycle — even if the cycle fails mid-way, record what happened
- [ ] **MUST NOT** use `nonce = w3.eth.get_transaction_count(address)` for nonce management in the loop — this causes nonce conflicts. Maintain nonce state in the NonceManager class
- [ ] **MUST NOT** submit a validation artifact with an empty hash — if the cycle produced no trade data, hash the cycle metadata (timestamp + cycle number + "SKIPPED")
- [ ] **MUST NOT** crash on Chainlink feed timeout — wrap all feed calls in try/except with retry logic

---

## Implementation Steps

### Step 1: Verify Phase 2 Is Complete — Run One Clean Trade

Before building the loop, verify the single-trade path is solid:

```bash
NETWORK=base_sepolia python agent/main.py trade
```

Check the output:
- ✅ Strategy Agent produces valid JSON signal
- ✅ Risk Agent returns APPROVED or REJECTED (not an error)
- ✅ If APPROVED: tx hash appears on `https://sepolia.basescan.org`
- ✅ Validation hash logged
- ✅ `agent/data/performance.json` updated

If any of these fail, fix Phase 2 issues first. Do not proceed to Step 2 until `main.py trade` is clean.

### Step 2: Build `agent/core/nonce_manager.py`

Reliable nonce management is the #1 cause of failed tx loops. Build a dedicated manager:

```python
# agent/core/nonce_manager.py

import threading
from web3 import Web3

class NonceManager:
    """Thread-safe nonce manager that avoids relying on pending tx count."""
    
    def __init__(self, w3: Web3, address: str):
        self.w3 = w3
        self.address = address
        self._lock = threading.Lock()
        self._nonce: int | None = None
    
    def initialize(self) -> int:
        """Sync nonce from chain. Call once at loop start."""
        with self._lock:
            self._nonce = self.w3.eth.get_transaction_count(self.address, "latest")
            return self._nonce
    
    def get_and_increment(self) -> int:
        """Get current nonce and increment for next tx. Thread-safe."""
        with self._lock:
            if self._nonce is None:
                self.initialize()
            nonce = self._nonce
            self._nonce += 1
            return nonce
    
    def reset_from_chain(self):
        """Re-sync from chain after a failed tx or nonce conflict."""
        with self._lock:
            confirmed = self.w3.eth.get_transaction_count(self.address, "latest")
            self._nonce = confirmed
            return self._nonce
```

Import and use `NonceManager` in `eip712_signer.py` and the execution agent — replace any `w3.eth.get_transaction_count()` calls inside the loop.

### Step 3: Build `agent/core/trade_logger.py`

```python
# agent/core/trade_logger.py

import csv
import json
from pathlib import Path
from datetime import datetime, timezone

TRADES_JSON = Path(__file__).parent.parent / "data" / "trades.json"
TRADES_CSV = Path(__file__).parent.parent / "data" / "trades.csv"

CSV_FIELDS = [
    "timestamp", "cycle", "action", "token_in", "token_out",
    "amount_in_usd", "amount_out_usd", "pnl_usd", "tx_hash",
    "validation_hash", "status", "error"
]

def log_trade(cycle: int, action: str, token_in: str, token_out: str,
              amount_in_usd: float, amount_out_usd: float,
              tx_hash: str | None, validation_hash: str | None,
              status: str, error: str | None = None) -> dict:
    """Append a trade record to both JSON and CSV logs."""
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": cycle,
        "action": action,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in_usd": amount_in_usd,
        "amount_out_usd": amount_out_usd,
        "pnl_usd": amount_out_usd - amount_in_usd,
        "tx_hash": tx_hash,
        "validation_hash": validation_hash,
        "status": status,   # "EXECUTED", "REJECTED", "SKIPPED", "ERROR"
        "error": error,
    }
    
    # JSON log — append to array
    TRADES_JSON.parent.mkdir(exist_ok=True)
    trades = []
    if TRADES_JSON.exists():
        trades = json.loads(TRADES_JSON.read_text())
    trades.append(record)
    TRADES_JSON.write_text(json.dumps(trades, indent=2))
    
    # CSV log — append row
    write_header = not TRADES_CSV.exists()
    with open(TRADES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: record.get(k, "") for k in CSV_FIELDS})
    
    return record
```

Call `log_trade()` at the end of every cycle — including `REJECTED` and `SKIPPED` cycles.

### Step 4: Build Gas Escalation + Retry Logic

In `agent/tools/uniswap_router.py`, wrap `submit_trade_intent()` with retry logic:

```python
import time
from web3.exceptions import TransactionNotFound

MAX_RETRIES = 3
GAS_ESCALATION_FACTOR = 1.20  # 20% more gas each retry

def submit_with_retry(intent, signature, w3, private_key, router_address, nonce_manager) -> dict:
    """Submit a TradeIntent with automatic gas escalation and nonce reset on failure."""
    
    base_gas_price = w3.eth.gas_price
    
    for attempt in range(MAX_RETRIES):
        gas_price = int(base_gas_price * (GAS_ESCALATION_FACTOR ** attempt))
        nonce = nonce_manager.get_and_increment()
        
        try:
            result = submit_trade_intent(
                intent=intent,
                signature=signature,
                w3=w3,
                private_key=private_key,
                router_address=router_address,
                nonce=nonce,
                gas_price=gas_price,
            )
            return result  # success
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "nonce too low" in error_str or "nonce" in error_str:
                # Nonce conflict — re-sync from chain
                print(f"[retry {attempt+1}] Nonce conflict. Re-syncing from chain...")
                nonce_manager.reset_from_chain()
                time.sleep(2)
                
            elif "replacement transaction underpriced" in error_str:
                # Gas too low — escalation already applied next loop
                print(f"[retry {attempt+1}] Gas too low. Escalating...")
                time.sleep(3)
                
            else:
                print(f"[retry {attempt+1}] Unknown error: {e}")
                time.sleep(5)
            
            if attempt == MAX_RETRIES - 1:
                raise  # Re-raise on final attempt
    
    raise RuntimeError("Exhausted all retries")
```

### Step 5: Implement `python agent/main.py loop`

Add the `loop` command to `main.py`:

```python
LOOP_INTERVAL_SECONDS = 15 * 60  # 15 minutes

def cmd_loop():
    """Run the trading loop continuously with 15-minute cycles."""
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    import signal
    
    console = Console()
    nonce_manager = NonceManager(w3, settings.agent_wallet_address)
    nonce_manager.initialize()
    
    cycle = 0
    running = True
    
    def handle_sigint(signum, frame):
        nonlocal running
        console.print("\n[yellow]Shutting down loop gracefully (Ctrl+C)...[/yellow]")
        running = False
    
    signal.signal(signal.SIGINT, handle_sigint)
    
    console.print(f"[bold green]ChronoTrader loop started.[/bold green] 15-min cycles. Ctrl+C to stop.")
    
    while running:
        cycle += 1
        cycle_start = time.time()
        
        console.rule(f"[cyan]Cycle {cycle} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}[/cyan]")
        
        try:
            # Run one full trade cycle
            result = run_trade_cycle(cycle=cycle, nonce_manager=nonce_manager)
            
            # Log the result
            log_trade(
                cycle=cycle,
                action=result["action"],
                token_in=result["token_in"],
                token_out=result["token_out"],
                amount_in_usd=result["amount_in_usd"],
                amount_out_usd=result["amount_out_usd"],
                tx_hash=result.get("tx_hash"),
                validation_hash=result.get("validation_hash"),
                status=result["status"],
            )
            
            # Always submit a validation artifact (even for REJECTED/SKIPPED)
            submit_validation_artifact(cycle=cycle, result=result)
            
            # Update and display metrics
            if result["status"] == "EXECUTED":
                metrics = update_metrics(result, result["amount_in_usd"], result["amount_out_usd"])
                print_metrics_summary(metrics)
        
        except Exception as e:
            console.print(f"[red]Cycle {cycle} failed: {e}[/red]")
            log_trade(cycle=cycle, action="UNKNOWN", token_in="", token_out="",
                      amount_in_usd=0, amount_out_usd=0, tx_hash=None,
                      validation_hash=None, status="ERROR", error=str(e))
            # Always submit a validation artifact even on error
            submit_validation_artifact(cycle=cycle, result={"status": "ERROR", "error": str(e)})
        
        # Wait for next cycle
        elapsed = time.time() - cycle_start
        wait_time = max(0, LOOP_INTERVAL_SECONDS - elapsed)
        
        if running:
            console.print(f"[dim]Next cycle in {int(wait_time)}s (cycle {cycle+1})[/dim]")
            # Wait in 1-second increments so Ctrl+C is responsive
            for _ in range(int(wait_time)):
                if not running:
                    break
                time.sleep(1)
    
    console.print("[bold green]Loop stopped. State saved.[/bold green]")
```

### Step 6: Implement `submit_validation_artifact()`

This must run after EVERY cycle — success, rejection, skip, or error:

```python
def submit_validation_artifact(cycle: int, result: dict):
    """Hash cycle data and submit to ValidationRegistry on-chain."""
    import hashlib
    
    # Build the artifact data
    artifact = {
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat(),
        "status": result.get("status"),
        "tx_hash": result.get("tx_hash"),
        "action": result.get("action", "UNKNOWN"),
        "pnl_usd": result.get("amount_out_usd", 0) - result.get("amount_in_usd", 0),
        "agent_id": int(os.getenv("AGENT_ID", 0)),
    }
    
    # SHA-256 hash of the artifact JSON
    artifact_json = json.dumps(artifact, sort_keys=True)
    artifact_hash = "0x" + hashlib.sha256(artifact_json.encode()).hexdigest()
    
    # Submit to ValidationRegistry
    try:
        tx_hash = erc8004_client.submit_validation_artifact(
            agent_id=artifact["agent_id"],
            data_hash=artifact_hash,
        )
        print(f"[green]Validation artifact submitted: {artifact_hash[:12]}... tx: {tx_hash[:12]}...[/green]")
    except Exception as e:
        # Never fail the loop because of a validation submission error
        print(f"[yellow]Validation artifact submission failed (non-fatal): {e}[/yellow]")
    
    return artifact_hash
```

### Step 7: Verify Chainlink Feeds Are Live

Check `agent/tools/chainlink_feed.py`. Ensure it:
1. Uses the correct Base Sepolia feed addresses (check `docs/onboarding.md` resources)
2. Has retry logic (3 retries with 2s backoff)
3. Returns prices in USD with 8 decimal normalization (Chainlink uses `1e8`)
4. Logs a warning (not a crash) if price is stale (more than 1 hour old based on `updatedAt`)

Test independently:
```bash
python -c "
from agent.tools.chainlink_feed import ChainlinkFeedClient
from dotenv import load_dotenv
load_dotenv()
client = ChainlinkFeedClient(rpc_url='https://sepolia.base.org')
print('ETH/USD:', client.get_price('ETH'))
print('BTC/USD:', client.get_price('BTC'))
"
```

Both must return real numbers (not None, not 0).

### Step 8: Run 3 Consecutive Loop Cycles

Test the loop with a shortened interval for verification:

```bash
# Temporarily set LOOP_INTERVAL_SECONDS = 30 (30 seconds) for testing
LOOP_INTERVAL_SECONDS=30 NETWORK=base_sepolia python agent/main.py loop
```

After 3 cycles, verify:
```bash
# Check trade history
cat agent/data/trades.json | python -m json.tool | head -60

# Check CSV
cat agent/data/trades.csv

# Check performance metrics
cat agent/data/performance.json | python -m json.tool

# Check Base Sepolia explorer for tx hashes
```

Restore `LOOP_INTERVAL_SECONDS = 15 * 60` before finishing.

### Step 9: Update `docs/onboarding.md`

For each completed Phase 3 task:
- Change status to `✅ DONE`
- Add the first live trade tx hash in Notes
- Add the number of cycles run in the loop Notes
- Add the Chainlink feed addresses used in Notes

Example:
```markdown
| First live trade executed on Base Sepolia sandbox | ✅ DONE | tx: 0xabc..., block: 12345678 |
| Continuous trading loop running | ✅ DONE | Tested 5 cycles at 30s interval |
```

---

## Definition of Done

Phase 3 is complete when ALL of the following are true:

- [ ] All Phase 1 and Phase 2 tasks in `docs/onboarding.md` are `✅ DONE`
- [ ] `python agent/main.py trade` executes a live trade with a real tx hash on `sepolia.basescan.org`
- [ ] `python agent/main.py loop` runs for at least 3 consecutive cycles without crashing
- [ ] `agent/data/trades.json` exists with at least 3 trade records (can include REJECTED/SKIPPED)
- [ ] `agent/data/trades.csv` exists with same records in CSV format
- [ ] `agent/data/performance.json` shows correct PnL, Sharpe, and drawdown after cycles
- [ ] ValidationRegistry on-chain has artifact hashes for each cycle (verify with `cast call`)
- [ ] Chainlink ETH/USD and BTC/USD feeds return live prices (no mocks)
- [ ] Ctrl+C on the loop exits cleanly without losing any trade history
- [ ] `NonceManager` is in use — no raw `get_transaction_count()` calls inside the loop
- [ ] All Phase 3 tasks in `docs/onboarding.md` show `✅ DONE`
- [ ] `docs/onboarding.md` Phase 3 "What's next" confirms Phase 4 is unblocked

---

## Resources

- Base Sepolia RPC: `https://sepolia.base.org`
- Base Sepolia Explorer: `https://sepolia.basescan.org`
- Chainlink Base Sepolia feeds: `https://docs.chain.link/data-feeds/price-feeds/addresses?network=base-sepolia`
  - ETH/USD: `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1`
  - BTC/USD: `0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298`
- web3.py gas estimation: `w3.eth.estimate_gas(tx)` — always add 20% buffer
- ERC-8004 ValidationRegistry: address from `.env` `VALIDATION_REGISTRY_ADDRESS`
- Rich library docs: `https://rich.readthedocs.io`
- Hackathon page: `https://lablab.ai/ai-hackathons/ai-trading-agents-erc-8004`
