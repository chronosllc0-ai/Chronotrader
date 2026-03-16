// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {RiskManager} from "../src/trading/RiskManager.sol";

contract RiskManagerTest is Test {
    IdentityRegistry public identity;
    RiskManager public riskManager;

    address public agentOwner = address(0x1);
    uint256 public agentId;

    function setUp() public {
        identity = new IdentityRegistry();
        riskManager = new RiskManager(address(identity));

        // Register an agent
        vm.prank(agentOwner);
        agentId = identity.register("ipfs://QmTestAgent");

        // Set risk params
        vm.prank(agentOwner);
        riskManager.setRiskParams(
            agentId,
            1000e18,  // $1000 max position
            500,      // 5% max daily loss
            1500,     // 15% max drawdown
            50        // 50 trades/day limit
        );

        // Initialize capital
        vm.prank(agentOwner);
        riskManager.initializeAgent(agentId, 10000e18); // $10,000 starting capital
    }

    function test_CheckRisk_Approved() public view {
        (bool approved, string memory reason) = riskManager.checkRisk(agentId, 500e18);
        assertTrue(approved);
        assertEq(bytes(reason).length, 0);
    }

    function test_CheckRisk_ExceedsPositionSize() public view {
        (bool approved, string memory reason) = riskManager.checkRisk(agentId, 2000e18);
        assertFalse(approved);
        assertEq(reason, "Exceeds max position size");
    }

    function test_CheckRisk_NoParams() public view {
        // Agent 999 has no risk params set
        (bool approved, string memory reason) = riskManager.checkRisk(999, 100e18);
        assertFalse(approved);
        assertEq(reason, "Risk params not set");
    }

    function test_UpdateCapital() public {
        riskManager.updateCapital(agentId, 10500e18); // Profit

        (uint256 peakCapital,,,,) = riskManager.agentStates(agentId);
        assertEq(peakCapital, 10500e18); // Peak updated
    }

    function test_SetRiskParams_RevertNotOwner() public {
        vm.prank(address(0x999));
        vm.expectRevert("RiskManager: not agent owner");
        riskManager.setRiskParams(agentId, 100e18, 100, 100, 10);
    }
}
