// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IReputationRegistry} from "../interfaces/IReputationRegistry.sol";
import {IdentityRegistry} from "./IdentityRegistry.sol";

/**
 * @title ReputationRegistry
 * @notice ERC-8004 Reputation Registry — standardized feedback and trust scoring
 * @dev Server agents authorize clients to submit feedback, building on-chain reputation
 */
contract ReputationRegistry is IReputationRegistry {
    IdentityRegistry public immutable identityRegistry;

    /// @dev serverAgentId => clientAgentId => feedbackHash => authorized
    mapping(uint256 => mapping(uint256 => mapping(bytes32 => bool))) public feedbackAuthorizations;

    /// @dev agentId => cumulative score
    mapping(uint256 => uint256) public totalScore;

    /// @dev agentId => feedback count
    mapping(uint256 => uint256) public feedbackCount;

    /// @dev agentId => array of individual scores
    mapping(uint256 => uint8[]) public scoreHistory;

    constructor(address _identityRegistry) {
        identityRegistry = IdentityRegistry(_identityRegistry);
    }

    /// @inheritdoc IReputationRegistry
    function authorizeFeedback(uint256 clientAgentId, bytes32 feedbackHash) external {
        // Caller must own an agent — find their agent ID
        // For simplicity, we use msg.sender as the server agent's wallet
        // In production, would look up agentId from wallet mapping
        feedbackAuthorizations[_getAgentIdForWallet(msg.sender)][clientAgentId][feedbackHash] = true;

        emit FeedbackAuthorized(
            _getAgentIdForWallet(msg.sender),
            clientAgentId,
            feedbackHash
        );
    }

    /// @inheritdoc IReputationRegistry
    function submitFeedback(
        uint256 serverAgentId,
        uint8 score,
        string calldata metadata
    ) external {
        require(score <= 100, "ReputationRegistry: score must be 0-100");

        uint256 clientAgentId = _getAgentIdForWallet(msg.sender);
        require(clientAgentId > 0, "ReputationRegistry: caller not a registered agent");

        totalScore[serverAgentId] += score;
        feedbackCount[serverAgentId]++;
        scoreHistory[serverAgentId].push(score);

        emit FeedbackSubmitted(serverAgentId, clientAgentId, score, metadata);
    }

    /// @notice Get an agent's average reputation score
    /// @param agentId The agent to query
    /// @return averageScore The average score (0-100), 0 if no feedback
    function getAverageScore(uint256 agentId) external view returns (uint256 averageScore) {
        if (feedbackCount[agentId] == 0) return 0;
        return totalScore[agentId] / feedbackCount[agentId];
    }

    /// @notice Get an agent's reputation summary
    /// @param agentId The agent to query
    /// @return total Cumulative score
    /// @return count Number of feedbacks
    /// @return average Average score
    function getReputation(uint256 agentId) external view returns (
        uint256 total,
        uint256 count,
        uint256 average
    ) {
        total = totalScore[agentId];
        count = feedbackCount[agentId];
        average = count > 0 ? total / count : 0;
    }

    /// @dev Helper to get agentId for a wallet address (simplified lookup)
    function _getAgentIdForWallet(address wallet) internal view returns (uint256) {
        // Iterate through agents to find matching wallet
        // In production, use a reverse mapping for O(1) lookup
        uint256 count = identityRegistry.agentCount();
        for (uint256 i = 1; i <= count; i++) {
            if (identityRegistry.agentWallets(i) == wallet) {
                return i;
            }
        }
        return 0;
    }
}
