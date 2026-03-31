"""
ERC-8004 Registry Tools
Provides CrewAI-compatible tools for interacting with ERC-8004 registries
"""

import json
from typing import Optional
from web3 import Web3
from eth_account import Account
try:
    from crewai.tools import tool
except Exception:
    try:
        from crewai_tools import tool  # type: ignore
    except Exception:
        def tool(_name):
            def deco(fn):
                return fn
            return deco


# ABI snippets for registry interactions
IDENTITY_REGISTRY_ABI = json.loads("""[
    {
        "inputs": [{"name": "uri", "type": "string"}],
        "name": "register",
        "outputs": [{"name": "agentId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "agentCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "ownerOfAgent",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]""")

REPUTATION_REGISTRY_ABI = json.loads("""[
    {
        "inputs": [
            {"name": "serverAgentId", "type": "uint256"},
            {"name": "score", "type": "uint8"},
            {"name": "metadata", "type": "string"}
        ],
        "name": "submitFeedback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "getReputation",
        "outputs": [
            {"name": "total", "type": "uint256"},
            {"name": "count", "type": "uint256"},
            {"name": "average", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]""")

VALIDATION_REGISTRY_ABI = json.loads("""[
    {
        "inputs": [
            {"name": "validatorAgentId", "type": "uint256"},
            {"name": "serverAgentId", "type": "uint256"},
            {"name": "dataHash", "type": "bytes32"}
        ],
        "name": "validationRequest",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "dataHash", "type": "bytes32"}],
        "name": "getValidation",
        "outputs": [
            {
                "components": [
                    {"name": "validatorAgentId", "type": "uint256"},
                    {"name": "serverAgentId", "type": "uint256"},
                    {"name": "dataHash", "type": "bytes32"},
                    {"name": "score", "type": "uint8"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "completed", "type": "bool"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]""")


class ERC8004Client:
    """Client for interacting with ERC-8004 registries on-chain"""

    def __init__(self, rpc_url: str, private_key: str, addresses: dict):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.addresses = addresses

        # Initialize contracts
        self.identity = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["identity"]),
            abi=IDENTITY_REGISTRY_ABI,
        )
        self.reputation = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["reputation"]),
            abi=REPUTATION_REGISTRY_ABI,
        )
        self.validation = self.w3.eth.contract(
            address=Web3.to_checksum_address(addresses["validation"]),
            abi=VALIDATION_REGISTRY_ABI,
        )

    def _send_tx(self, tx_func):
        """Build, sign, and send a transaction"""
        tx = tx_func.build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt

    def register_agent(self, agent_card_uri: str) -> int:
        """Register an agent on the Identity Registry"""
        receipt = self._send_tx(self.identity.functions.register(agent_card_uri))
        # Parse agentId from logs
        logs = self.identity.events.AgentRegistered().process_receipt(receipt)
        if logs:
            return logs[0]["args"]["agentId"]
        return 0

    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return self.identity.functions.agentCount().call()

    def get_reputation(self, agent_id: int) -> dict:
        """Get an agent's reputation summary"""
        total, count, average = self.reputation.functions.getReputation(agent_id).call()
        return {"total": total, "count": count, "average": average}

    def submit_feedback(self, server_agent_id: int, score: int, metadata: str):
        """Submit reputation feedback for an agent"""
        return self._send_tx(
            self.reputation.functions.submitFeedback(server_agent_id, score, metadata)
        )


    def submit_reputation_score(self, agent_id: int, score_bps: int, metadata: str) -> str:
        """Submit 0-10000 basis-point score by mapping to uint8 expected by contract."""
        mapped = max(1, min(99, score_bps // 100))
        receipt = self.submit_feedback(agent_id, mapped, metadata)
        return receipt["transactionHash"].hex()

    def request_validation(
        self, validator_id: int, server_id: int, data_hash: bytes
    ):
        """Request validation for agent work"""
        return self._send_tx(
            self.validation.functions.validationRequest(
                validator_id, server_id, data_hash
            )
        )


# ── CrewAI Tool Wrappers ────────────────────────────────────────────────────

_client: Optional[ERC8004Client] = None


def get_erc8004_client() -> Optional[ERC8004Client]:
    return _client


def init_erc8004_tools(rpc_url: str, private_key: str, addresses: dict):
    """Initialize the ERC-8004 client for tool usage"""
    global _client
    _client = ERC8004Client(rpc_url, private_key, addresses)


@tool("Register Agent on ERC-8004")
def register_agent(agent_card_uri: str) -> str:
    """Register the agent on the ERC-8004 Identity Registry.
    Input: IPFS URI pointing to the agent card JSON.
    Returns: The assigned agent ID."""
    if not _client:
        return "Error: ERC-8004 client not initialized"
    agent_id = _client.register_agent(agent_card_uri)
    return f"Agent registered successfully with ID: {agent_id}"


@tool("Check Agent Reputation")
def check_reputation(agent_id: int) -> str:
    """Check an agent's on-chain reputation score.
    Input: The agent ID to query.
    Returns: Reputation summary with total score, feedback count, and average."""
    if not _client:
        return "Error: ERC-8004 client not initialized"
    rep = _client.get_reputation(agent_id)
    return f"Agent {agent_id} reputation — Average: {rep['average']}/100, Feedbacks: {rep['count']}, Total: {rep['total']}"
