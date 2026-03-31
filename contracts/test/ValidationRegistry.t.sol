// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {ValidationRegistry} from "../src/registries/ValidationRegistry.sol";

contract ValidationRegistryTest is Test {
    IdentityRegistry public identity;
    ValidationRegistry public validation;

    address public validatorOwner = address(0x1);
    address public serverOwner = address(0x2);
    uint256 public validatorAgentId;
    uint256 public serverAgentId;

    bytes32 public testHash = keccak256("test_data_hash");

    function setUp() public {
        identity = new IdentityRegistry();
        validation = new ValidationRegistry(address(identity));

        // Register validator agent
        vm.prank(validatorOwner);
        validatorAgentId = identity.register("ipfs://QmValidatorAgent");

        // Register server agent
        vm.prank(serverOwner);
        serverAgentId = identity.register("ipfs://QmServerAgent");
    }

    function test_ValidationRequest() public {
        // Server requests validation from validator
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // Verify record stored
        ValidationRegistry.ValidationRecord memory record = validation.getValidation(testHash);
        assertEq(record.validatorAgentId, validatorAgentId);
        assertEq(record.serverAgentId, serverAgentId);
        assertEq(record.dataHash, testHash);
        assertFalse(record.completed);
    }

    function test_ValidationResponse() public {
        // Server requests validation
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // Validator submits response
        vm.prank(validatorOwner);
        validation.validationResponse(serverAgentId, testHash, 85);

        // Verify record updated
        ValidationRegistry.ValidationRecord memory record = validation.getValidation(testHash);
        assertTrue(record.completed);
        assertEq(record.score, 85);
    }

    function test_GetAgentValidationCount() public {
        bytes32 hash1 = keccak256("data_1");
        bytes32 hash2 = keccak256("data_2");

        // Server requests multiple validations
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, hash1);

        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, hash2);

        // Check count
        assertEq(validation.getAgentValidationCount(serverAgentId), 2);
    }

    function test_ValidationRequest_RevertAlreadyRequested() public {
        // First request succeeds
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // Second request with same hash fails
        vm.prank(serverOwner);
        vm.expectRevert("ValidationRegistry: already requested");
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);
    }

    function test_ValidationResponse_RevertNoPendingRequest() public {
        vm.prank(validatorOwner);
        vm.expectRevert("ValidationRegistry: no pending request");
        validation.validationResponse(serverAgentId, testHash, 85);
    }

    function test_ValidationResponse_RevertAlreadyValidated() public {
        // Request validation
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // First response succeeds
        vm.prank(validatorOwner);
        validation.validationResponse(serverAgentId, testHash, 85);

        // Second response fails
        vm.prank(validatorOwner);
        vm.expectRevert("ValidationRegistry: already validated");
        validation.validationResponse(serverAgentId, testHash, 90);
    }

    function test_ValidationResponse_RevertInvalidScore() public {
        // Request validation
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // Invalid score > 100
        vm.prank(validatorOwner);
        vm.expectRevert("ValidationRegistry: score must be 0-100");
        validation.validationResponse(serverAgentId, testHash, 101);
    }

    function test_ValidationResponse_RevertNotAssignedValidator() public {
        // Server requests validation from validatorAgentId
        vm.prank(serverOwner);
        validation.validationRequest(validatorAgentId, serverAgentId, testHash);

        // Server (not validator) tries to respond
        vm.prank(serverOwner);
        vm.expectRevert("ValidationRegistry: not assigned validator");
        validation.validationResponse(serverAgentId, testHash, 85);
    }
}
