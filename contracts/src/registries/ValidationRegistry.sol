// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IValidationRegistry} from "../interfaces/IValidationRegistry.sol";
import {IdentityRegistry} from "./IdentityRegistry.sol";

/**
 * @title ValidationRegistry
 * @notice ERC-8004 Validation Registry — verifiable proof of agent work
 * @dev Agents submit data hashes for validation; validators score 0-100 on-chain
 */
contract ValidationRegistry is IValidationRegistry {
    IdentityRegistry public immutable identityRegistry;

    struct ValidationRecord {
        uint256 validatorAgentId;
        uint256 serverAgentId;
        bytes32 dataHash;
        uint8 score;
        uint256 timestamp;
        bool completed;
    }

    /// @dev dataHash => ValidationRecord
    mapping(bytes32 => ValidationRecord) public validations;

    /// @dev agentId => array of data hashes submitted for validation
    mapping(uint256 => bytes32[]) public agentValidations;

    /// @dev Track pending validation requests
    mapping(bytes32 => bool) public pendingRequests;

    constructor(address _identityRegistry) {
        identityRegistry = IdentityRegistry(_identityRegistry);
    }

    /// @inheritdoc IValidationRegistry
    function validationRequest(
        uint256 validatorAgentId,
        uint256 serverAgentId,
        bytes32 dataHash
    ) external {
        require(!pendingRequests[dataHash], "ValidationRegistry: already requested");

        pendingRequests[dataHash] = true;
        validations[dataHash] = ValidationRecord({
            validatorAgentId: validatorAgentId,
            serverAgentId: serverAgentId,
            dataHash: dataHash,
            score: 0,
            timestamp: block.timestamp,
            completed: false
        });

        agentValidations[serverAgentId].push(dataHash);

        emit ValidationRequested(validatorAgentId, serverAgentId, dataHash);
    }

    /// @inheritdoc IValidationRegistry
    function validationResponse(
        uint256 serverAgentId,
        bytes32 dataHash,
        uint8 score
    ) external {
        require(score <= 100, "ValidationRegistry: score must be 0-100");
        require(pendingRequests[dataHash], "ValidationRegistry: no pending request");

        ValidationRecord storage record = validations[dataHash];
        require(!record.completed, "ValidationRegistry: already validated");

        // Verify caller is the assigned validator
        uint256 callerAgentId = _getAgentIdForWallet(msg.sender);
        require(
            callerAgentId == record.validatorAgentId,
            "ValidationRegistry: not assigned validator"
        );

        record.score = score;
        record.completed = true;
        record.timestamp = block.timestamp;

        emit ValidationResponse(callerAgentId, serverAgentId, dataHash, score);
    }

    /// @notice Get validation record for a data hash
    function getValidation(bytes32 dataHash) external view returns (ValidationRecord memory) {
        return validations[dataHash];
    }

    /// @notice Get all validation hashes for an agent
    function getAgentValidationCount(uint256 agentId) external view returns (uint256) {
        return agentValidations[agentId].length;
    }

    /// @dev Helper to get agentId for a wallet address
    function _getAgentIdForWallet(address wallet) internal view returns (uint256) {
        uint256 count = identityRegistry.agentCount();
        for (uint256 i = 1; i <= count; i++) {
            if (identityRegistry.agentWallets(i) == wallet) {
                return i;
            }
        }
        return 0;
    }
}
