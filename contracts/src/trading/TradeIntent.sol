// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title TradeIntent
 * @notice EIP-712 typed data structure for signed trade intents
 * @dev Agents sign trade intents off-chain; Risk Router verifies and executes
 */
contract TradeIntent {
    bytes32 public constant TRADE_INTENT_TYPEHASH = keccak256(
        "TradeIntent(uint256 agentId,address tokenIn,address tokenOut,uint256 amountIn,uint256 minAmountOut,uint256 deadline,uint256 nonce,bytes32 strategyHash)"
    );

    bytes32 public immutable DOMAIN_SEPARATOR;

    /// @dev agentId => nonce (replay protection)
    mapping(uint256 => uint256) public nonces;

    struct Intent {
        uint256 agentId;       // ERC-8004 agent ID
        address tokenIn;       // Token to sell
        address tokenOut;      // Token to buy
        uint256 amountIn;      // Amount to sell
        uint256 minAmountOut;  // Minimum amount to receive (slippage protection)
        uint256 deadline;      // Expiry timestamp
        uint256 nonce;         // Replay protection
        bytes32 strategyHash;  // Hash of the strategy rationale (stored on IPFS)
    }

    constructor() {
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256("ChronoTrader"),
                keccak256("1"),
                block.chainid,
                address(this)
            )
        );
    }

    /// @notice Hash a trade intent for EIP-712 signing
    /// @param intent The trade intent to hash
    /// @return The EIP-712 typed data hash
    function hashIntent(Intent calldata intent) public view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            TRADE_INTENT_TYPEHASH,
            intent.agentId,
            intent.tokenIn,
            intent.tokenOut,
            intent.amountIn,
            intent.minAmountOut,
            intent.deadline,
            intent.nonce,
            intent.strategyHash
        ));

        return keccak256(abi.encodePacked(
            "\x19\x01",
            DOMAIN_SEPARATOR,
            structHash
        ));
    }

    /// @notice Verify an EIP-712 signed trade intent
    /// @param intent The trade intent
    /// @param v Signature v
    /// @param r Signature r
    /// @param s Signature s
    /// @return signer The recovered signer address
    function verifyIntent(
        Intent calldata intent,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public view returns (address signer) {
        bytes32 digest = hashIntent(intent);
        signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "TradeIntent: invalid signature");
    }

    /// @notice Get and increment nonce for an agent
    function useNonce(uint256 agentId) internal returns (uint256 current) {
        current = nonces[agentId];
        nonces[agentId] = current + 1;
    }
}
