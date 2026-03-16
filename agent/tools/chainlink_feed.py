"""
Chainlink Price Feed Tools
Provides real-time price data for trading strategy decisions
"""

from web3 import Web3
from crewai_tools import tool
from typing import Optional

# Chainlink Aggregator V3 ABI (minimal)
AGGREGATOR_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "description",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Known Chainlink feed addresses on Base Sepolia
# Update these with actual deployed addresses
FEEDS = {
    "ETH/USD": "0x4aDC67d868764f27A5A1C26528b1b1E67Ff6Cb03",
    "BTC/USD": "0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298",
}


class ChainlinkClient:
    """Client for reading Chainlink price feeds"""

    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

    def get_price(self, feed_address: str) -> dict:
        """Get latest price from a Chainlink feed"""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(feed_address),
            abi=AGGREGATOR_ABI,
        )

        decimals = contract.functions.decimals().call()
        description = contract.functions.description().call()
        round_data = contract.functions.latestRoundData().call()

        price = round_data[1] / (10**decimals)
        updated_at = round_data[3]

        return {
            "pair": description,
            "price": price,
            "decimals": decimals,
            "updated_at": updated_at,
            "raw_answer": round_data[1],
        }


_client: Optional[ChainlinkClient] = None


def init_chainlink_tools(rpc_url: str):
    """Initialize the Chainlink client"""
    global _client
    _client = ChainlinkClient(rpc_url)


@tool("Get Token Price")
def get_token_price(pair: str) -> str:
    """Get the current price of a token pair from Chainlink oracles.
    Input: Trading pair string like 'ETH/USD' or 'BTC/USD'.
    Returns: Current price with timestamp."""
    if not _client:
        return "Error: Chainlink client not initialized"

    pair = pair.upper().strip()
    if pair not in FEEDS:
        available = ", ".join(FEEDS.keys())
        return f"Error: Unknown pair '{pair}'. Available: {available}"

    try:
        data = _client.get_price(FEEDS[pair])
        return f"{data['pair']}: ${data['price']:,.2f} (updated: {data['updated_at']})"
    except Exception as e:
        return f"Error fetching price for {pair}: {str(e)}"


@tool("Get Market Data Summary")
def get_market_summary() -> str:
    """Get a summary of all available market prices from Chainlink oracles.
    Returns: Price summary for all tracked pairs."""
    if not _client:
        return "Error: Chainlink client not initialized"

    results = []
    for pair, address in FEEDS.items():
        try:
            data = _client.get_price(address)
            results.append(f"  {data['pair']}: ${data['price']:,.2f}")
        except Exception as e:
            results.append(f"  {pair}: Error - {str(e)}")

    return "Market Summary:\n" + "\n".join(results)
