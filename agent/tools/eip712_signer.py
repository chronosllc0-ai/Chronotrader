"""
EIP-712 Trade Intent Signing
Signs trade intents off-chain for submission to the Risk Router
"""

import time
from dataclasses import dataclass
from typing import Optional

from eth_account import Account
from eth_account.messages import encode_structured_data
from web3 import Web3


@dataclass
class TradeIntentData:
    """Represents a trade intent to be signed via EIP-712"""

    agent_id: int
    token_in: str
    token_out: str
    amount_in: int  # Wei
    min_amount_out: int  # Wei
    deadline: int  # Unix timestamp
    nonce: int
    strategy_hash: bytes  # 32 bytes


def build_eip712_message(
    intent: TradeIntentData,
    verifying_contract: str,
    chain_id: int,
) -> dict:
    """Build an EIP-712 typed data message for a TradeIntent"""

    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TradeIntent": [
                {"name": "agentId", "type": "uint256"},
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "minAmountOut", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "strategyHash", "type": "bytes32"},
            ],
        },
        "primaryType": "TradeIntent",
        "domain": {
            "name": "ChronoTrader",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": verifying_contract,
        },
        "message": {
            "agentId": intent.agent_id,
            "tokenIn": Web3.to_checksum_address(intent.token_in),
            "tokenOut": Web3.to_checksum_address(intent.token_out),
            "amountIn": intent.amount_in,
            "minAmountOut": intent.min_amount_out,
            "deadline": intent.deadline,
            "nonce": intent.nonce,
            "strategyHash": intent.strategy_hash,
        },
    }


def sign_trade_intent(
    intent: TradeIntentData,
    private_key: str,
    verifying_contract: str,
    chain_id: int,
) -> dict:
    """Sign a TradeIntent using EIP-712 typed data"""

    message = build_eip712_message(intent, verifying_contract, chain_id)
    encoded = encode_structured_data(message)

    account = Account.from_key(private_key)
    signed = account.sign_message(encoded)

    return {
        "intent": {
            "agentId": intent.agent_id,
            "tokenIn": intent.token_in,
            "tokenOut": intent.token_out,
            "amountIn": str(intent.amount_in),
            "minAmountOut": str(intent.min_amount_out),
            "deadline": intent.deadline,
            "nonce": intent.nonce,
            "strategyHash": "0x" + intent.strategy_hash.hex(),
        },
        "signature": {
            "v": signed.v,
            "r": "0x" + signed.r.to_bytes(32, "big").hex(),
            "s": "0x" + signed.s.to_bytes(32, "big").hex(),
        },
        "signer": account.address,
    }


def create_trade_intent(
    agent_id: int,
    token_in: str,
    token_out: str,
    amount_in_ether: float,
    slippage_bps: int = 50,  # 0.5% default
    deadline_minutes: int = 30,
    nonce: int = 0,
    strategy_rationale: str = "",
) -> TradeIntentData:
    """Helper to create a TradeIntent from human-readable inputs"""

    amount_in_wei = Web3.to_wei(amount_in_ether, "ether")
    min_out_wei = amount_in_wei * (10000 - slippage_bps) // 10000
    deadline = int(time.time()) + (deadline_minutes * 60)

    strategy_hash = Web3.solidity_keccak(["string"], [strategy_rationale])

    return TradeIntentData(
        agent_id=agent_id,
        token_in=Web3.to_checksum_address(token_in),
        token_out=Web3.to_checksum_address(token_out),
        amount_in=amount_in_wei,
        min_amount_out=min_out_wei,
        deadline=deadline,
        nonce=nonce,
        strategy_hash=strategy_hash,
    )
