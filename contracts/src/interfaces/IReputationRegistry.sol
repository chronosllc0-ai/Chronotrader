// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IReputationRegistry
 * @notice ERC-8004 Reputation Registry interface
 * @dev Tracks agent reputation through authorized feedback submissions
 */
interface IReputationRegistry {
    /// @notice Emitted when feedback is authorized
    event FeedbackAuthorized(
        uint256 indexed serverAgentId,
        uint256 indexed clientAgentId,
        bytes32 feedbackHash
    );

    /// @notice Emitted when feedback is submitted
    event FeedbackSubmitted(
        uint256 indexed serverAgentId,
        uint256 indexed clientAgentId,
        uint8 score,
        string metadata
    );

    /// @notice Server authorizes a client to submit feedback
    /// @param clientAgentId The client agent providing feedback
    /// @param feedbackHash Hash of the interaction context
    function authorizeFeedback(uint256 clientAgentId, bytes32 feedbackHash) external;

    /// @notice Client submits feedback for a server agent
    /// @param serverAgentId The agent being rated
    /// @param score Rating score (0-100)
    /// @param metadata Additional feedback context (JSON string)
    function submitFeedback(
        uint256 serverAgentId,
        uint8 score,
        string calldata metadata
    ) external;
}
