// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IIdentityRegistry
 * @notice ERC-8004 Identity Registry interface
 * @dev Agents register identity as ERC-721 tokens with metadata URIs
 */
interface IIdentityRegistry {
    /// @notice Emitted when a new agent is registered
    event AgentRegistered(uint256 indexed agentId, address indexed owner, string uri);

    /// @notice Emitted when an agent's URI is updated
    event AgentURIUpdated(uint256 indexed agentId, string uri);

    /// @notice Register a new agent and mint identity token
    /// @param uri The token URI pointing to the agent registration JSON
    /// @return agentId The newly minted agent ID
    function register(string calldata uri) external returns (uint256 agentId);

    /// @notice Update an existing agent's metadata URI
    /// @param agentId The agent ID to update
    /// @param uri The new token URI
    function updateURI(uint256 agentId, string calldata uri) external;

    /// @notice Get the owner of an agent ID
    /// @param agentId The agent ID
    /// @return The owner address
    function ownerOfAgent(uint256 agentId) external view returns (address);
}
