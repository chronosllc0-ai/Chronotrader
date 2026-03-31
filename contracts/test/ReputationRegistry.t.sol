// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {ReputationRegistry} from "../src/registries/ReputationRegistry.sol";

contract ReputationRegistryTest is Test {
    IdentityRegistry public identity;
    ReputationRegistry public reputation;

    address public serverOwner = address(0x1);
    address public clientOwner = address(0x2);
    uint256 public serverAgentId;
    uint256 public clientAgentId;

    function setUp() public {
        identity = new IdentityRegistry();
        reputation = new ReputationRegistry(address(identity));

        // Register server agent
        vm.prank(serverOwner);
        serverAgentId = identity.register("ipfs://QmServerAgent");

        // Register client agent
        vm.prank(clientOwner);
        clientAgentId = identity.register("ipfs://QmClientAgent");
    }

    function test_SubmitFeedback() public {
        // Client submits feedback to server
        vm.prank(clientOwner);
        reputation.submitFeedback(serverAgentId, 85, "Good trade execution");

        // Verify count increased
        (, uint256 count,) = reputation.getReputation(serverAgentId);
        assertEq(count, 1);

        // Verify average is 85
        (,, uint256 average) = reputation.getReputation(serverAgentId);
        assertEq(average, 85);
    }

    function test_GetReputation() public {
        // Submit multiple feedbacks
        vm.prank(clientOwner);
        reputation.submitFeedback(serverAgentId, 80, "First feedback");

        vm.prank(clientOwner);
        reputation.submitFeedback(serverAgentId, 90, "Second feedback");

        vm.prank(clientOwner);
        reputation.submitFeedback(serverAgentId, 100, "Third feedback");

        // Verify totals
        (uint256 total, uint256 count, uint256 average) = reputation.getReputation(serverAgentId);
        assertEq(total, 270); // 80 + 90 + 100
        assertEq(count, 3);
        assertEq(average, 90); // 270 / 3
    }

    function test_GetAverageScore() public {
        vm.prank(clientOwner);
        reputation.submitFeedback(serverAgentId, 75, "Feedback");

        uint256 avg = reputation.getAverageScore(serverAgentId);
        assertEq(avg, 75);
    }

    function test_GetAverageScore_NoFeedback() public {
        uint256 avg = reputation.getAverageScore(serverAgentId);
        assertEq(avg, 0);
    }

    function test_SubmitFeedback_RevertInvalidScore() public {
        vm.prank(clientOwner);
        vm.expectRevert("ReputationRegistry: score must be 0-100");
        reputation.submitFeedback(serverAgentId, 101, "Invalid score");
    }

    function test_SubmitFeedback_RevertNotRegisteredAgent() public {
        // Random address tries to submit feedback
        vm.prank(address(0x999));
        vm.expectRevert("ReputationRegistry: caller not a registered agent");
        reputation.submitFeedback(serverAgentId, 80, "Invalid caller");
    }

    function test_GetReputation_Empty() public {
        (uint256 total, uint256 count, uint256 average) = reputation.getReputation(serverAgentId);
        assertEq(total, 0);
        assertEq(count, 0);
        assertEq(average, 0);
    }
}
