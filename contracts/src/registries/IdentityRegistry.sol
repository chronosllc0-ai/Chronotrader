// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "lib/openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";
import {ERC721URIStorage} from "lib/openzeppelin-contracts/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {IIdentityRegistry} from "../interfaces/IIdentityRegistry.sol";

/**
 * @title IdentityRegistry
 * @notice ERC-8004 Identity Registry — portable, censorship-resistant agent identifiers
 * @dev Each agent is an ERC-721 token whose URI resolves to an agent registration JSON
 *
 * Agent Registration JSON follows the ERC-8004 spec:
 * {
 *   "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
 *   "name": "ChronoTrader",
 *   "description": "...",
 *   "services": [...],
 *   "supportedTrust": ["reputation", "crypto-economic"]
 * }
 */
contract IdentityRegistry is ERC721URIStorage, IIdentityRegistry {
    uint256 private _nextAgentId = 1;

    /// @dev agentId => agent wallet address (the address that operates on behalf of the agent)
    mapping(uint256 => address) public agentWallets;

    constructor() ERC721("ERC8004 Agent Identity", "AGENT") {}

    /// @inheritdoc IIdentityRegistry
    function register(string calldata uri) external returns (uint256 agentId) {
        require(msg.sender != address(0), "IdentityRegistry: zero address");
        agentId = _nextAgentId++;
        _safeMint(msg.sender, agentId);
        _setTokenURI(agentId, uri);
        agentWallets[agentId] = msg.sender;

        emit AgentRegistered(agentId, msg.sender, uri);
    }

    /// @inheritdoc IIdentityRegistry
    function updateURI(uint256 agentId, string calldata uri) external {
        require(ownerOf(agentId) == msg.sender, "IdentityRegistry: not owner");
        _setTokenURI(agentId, uri);

        emit AgentURIUpdated(agentId, uri);
    }

    /// @inheritdoc IIdentityRegistry
    function ownerOfAgent(uint256 agentId) external view returns (address) {
        return ownerOf(agentId);
    }

    /// @notice Set or update the wallet address that operates for this agent
    /// @param agentId The agent ID
    /// @param wallet The operating wallet address
    function setAgentWallet(uint256 agentId, address wallet) external {
        require(ownerOf(agentId) == msg.sender, "IdentityRegistry: not owner");
        agentWallets[agentId] = wallet;
    }

    /// @notice Get the current agent count
    function agentCount() external view returns (uint256) {
        return _nextAgentId - 1;
    }
}
