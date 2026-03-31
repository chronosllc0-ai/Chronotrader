"""
Uniswap V3 Router Tools
Provides DEX execution capabilities for trading strategies
"""

import json
from typing import Optional
from web3 import Web3
from eth_account import Account
from eth_abi import encode
try:
    from crewai_tools import tool
except Exception:
    def tool(_name):
        def deco(fn):
            return fn
        return deco


# Uniswap V3 SwapRouter ABI (minimal)
SWAP_ROUTER_ABI = json.loads("""[
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]""")

# ERC-20 ABI (minimal)
ERC20_ABI = json.loads("""[
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]""")


class UniswapClient:
    """Client for executing trades via Uniswap V3"""

    def __init__(self, rpc_url: str, private_key: str, router_address: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.router = self.w3.eth.contract(
            address=Web3.to_checksum_address(router_address),
            abi=SWAP_ROUTER_ABI,
        )
        self.router_address = Web3.to_checksum_address(router_address)

    def _send_tx(self, tx_func, value=0):
        """Build, sign, and send a transaction"""
        tx = tx_func.build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
                "value": value,
            }
        )
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt

    def approve_token(self, token_address: str, amount: int):
        """Approve router to spend tokens"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI,
        )
        return self._send_tx(
            token.functions.approve(self.router_address, amount)
        )

    def get_balance(self, token_address: str) -> dict:
        """Get token balance for the agent wallet"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI,
        )
        decimals = token.functions.decimals().call()
        balance_raw = token.functions.balanceOf(self.account.address).call()
        balance = balance_raw / (10**decimals)
        return {"raw": balance_raw, "formatted": balance, "decimals": decimals}

    def swap_exact_input(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        fee: int = 3000,
    ) -> dict:
        """Execute an exact input swap on Uniswap V3"""
        import time

        params = (
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            fee,
            self.account.address,
            int(time.time()) + 1800,  # 30 min deadline
            amount_in,
            min_amount_out,
            0,  # No price limit
        )

        receipt = self._send_tx(
            self.router.functions.exactInputSingle(params)
        )

        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "status": receipt["status"],
            "gas_used": receipt["gasUsed"],
        }


_client: Optional[UniswapClient] = None


def init_uniswap_tools(rpc_url: str, private_key: str, router_address: str):
    """Initialize the Uniswap client"""
    global _client
    _client = UniswapClient(rpc_url, private_key, router_address)


@tool("Execute Token Swap")
def execute_swap(
    token_in: str,
    token_out: str,
    amount_in_human: float,
    min_amount_out_human: float,
    decimals_in: int = 18,
    decimals_out: int = 18,
) -> str:
    """Execute a token swap on Uniswap V3.
    Inputs:
    - token_in: Address of token to sell
    - token_out: Address of token to buy
    - amount_in_human: Amount to sell (human-readable)
    - min_amount_out_human: Minimum amount to receive (slippage protection)
    - decimals_in/out: Token decimals (default 18)
    Returns: Transaction hash and status."""
    if not _client:
        return "Error: Uniswap client not initialized"

    try:
        amount_in = int(amount_in_human * (10**decimals_in))
        min_out = int(min_amount_out_human * (10**decimals_out))

        # Approve first
        _client.approve_token(token_in, amount_in)

        # Execute swap
        result = _client.swap_exact_input(
            token_in, token_out, amount_in, min_out
        )

        status = "Success" if result["status"] == 1 else "Failed"
        return f"Swap {status} — TX: {result['tx_hash']}, Gas: {result['gas_used']}"
    except Exception as e:
        return f"Error executing swap: {str(e)}"


@tool("Check Token Balance")
def check_balance(token_address: str) -> str:
    """Check the agent's balance of a specific token.
    Input: Token contract address.
    Returns: Current balance."""
    if not _client:
        return "Error: Uniswap client not initialized"

    try:
        bal = _client.get_balance(token_address)
        return f"Balance: {bal['formatted']:.6f} (raw: {bal['raw']}, decimals: {bal['decimals']})"
    except Exception as e:
        return f"Error checking balance: {str(e)}"
