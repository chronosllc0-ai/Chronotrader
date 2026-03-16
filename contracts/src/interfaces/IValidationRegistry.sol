// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IValidationRegistry
 * @notice ERC-8004 Validation Registry interface
 * @dev Enables agents to request and receive validation for their work
 */
interface IValidationRegistry {
    /// @notice Emitted when validation is requested
    event ValidationRequested(
        uint256 indexed validatorAgentId,
        uint256 indexed serverAgentId,
        bytes32 dataHash
    );

    /// @notice Emitted when validation response is submitted
    event ValidationResponse(
        uint256 indexed validatorAgentId,
        uint256 indexed serverAgentId,
        bytes32 dataHash,
        uint8 score
    );

    /// @notice Request validation from a validator agent
    /// @param validatorAgentId The validator agent ID
    /// @param serverAgentId The agent requesting validation
    /// @param dataHash Hash of the data to validate
    function validationRequest(
        uint256 validatorAgentId,
        uint256 serverAgentId,
        bytes32 dataHash
    ) external;

    /// @notice Submit validation response
    /// @param serverAgentId The agent that was validated
    /// @param dataHash The data hash being validated
    /// @param score Validation score (0-100)
    function validationResponse(
        uint256 serverAgentId,
        bytes32 dataHash,
        uint8 score
    ) external;
}
