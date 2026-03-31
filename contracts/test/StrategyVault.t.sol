// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {ERC20} from "lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {RiskManager} from "../src/trading/RiskManager.sol";
import {StrategyVault} from "../src/trading/StrategyVault.sol";

/// @dev Mock ERC20 token for testing
contract MockUSDC is ERC20 {
    constructor() ERC20("USD Coin", "USDC") {}

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

contract StrategyVaultTest is Test {
    IdentityRegistry public identity;
    RiskManager public riskManager;
    StrategyVault public vault;
    MockUSDC public usdc;

    address public agentOwner = address(0x1);
    address public user1 = address(0x10);
    address public user2 = address(0x20);
    uint256 public agentId;

    function setUp() public {
        identity = new IdentityRegistry();
        riskManager = new RiskManager(address(identity));
        usdc = new MockUSDC();
        vault = new StrategyVault(address(identity), address(riskManager), address(usdc));

        // Register an agent
        vm.prank(agentOwner);
        agentId = identity.register("ipfs://QmTestAgent");

        // Mint USDC to users
        usdc.mint(user1, 10000e6);
        usdc.mint(user2, 10000e6);
    }

    function test_Delegate() public {
        // User delegates capital to agent
        vm.startPrank(user1);
        usdc.approve(address(vault), 5000e6);
        vault.delegate(agentId, 5000e6);
        vm.stopPrank();

        // Check agent capital increased
        assertEq(vault.getAgentCapital(agentId), 5000e6);
    }

    function test_Withdraw() public {
        // First delegate capital
        vm.startPrank(user1);
        usdc.approve(address(vault), 5000e6);
        vault.delegate(agentId, 5000e6);
        vm.stopPrank();

        // Get delegation ID (first delegation)
        uint256 delegationId = 1;

        // User withdraws capital
        uint256 balanceBefore = usdc.balanceOf(user1);
        vm.prank(user1);
        vault.withdraw(delegationId);
        uint256 balanceAfter = usdc.balanceOf(user1);

        // Verify withdrawal
        assertEq(balanceAfter - balanceBefore, 5000e6);
        assertEq(vault.getAgentCapital(agentId), 0);
    }

    function test_GetAgentCapital() public {
        // Multiple users delegate
        vm.startPrank(user1);
        usdc.approve(address(vault), 3000e6);
        vault.delegate(agentId, 3000e6);
        vm.stopPrank();

        vm.startPrank(user2);
        usdc.approve(address(vault), 2000e6);
        vault.delegate(agentId, 2000e6);
        vm.stopPrank();

        // Check total capital
        assertEq(vault.getAgentCapital(agentId), 5000e6);
    }

    function test_Delegate_RevertZeroAmount() public {
        vm.prank(user1);
        usdc.approve(address(vault), 10000e6);
        
        vm.expectRevert("StrategyVault: zero amount");
        vault.delegate(agentId, 0);
    }

    function test_Delegate_RevertUnregisteredAgent() public {
        vm.prank(user1);
        usdc.approve(address(vault), 10000e6);
        
        // ERC721NonexistentToken reverts when querying non-existent agent
        vm.expectRevert(abi.encodeWithSignature("ERC721NonexistentToken(uint256)", 9999));
        vault.delegate(9999, 1000e6);
    }

    function test_Withdraw_RevertNotDelegator() public {
        // User1 delegates
        vm.startPrank(user1);
        usdc.approve(address(vault), 5000e6);
        vault.delegate(agentId, 5000e6);
        vm.stopPrank();

        // User2 tries to withdraw
        vm.prank(user2);
        vm.expectRevert("StrategyVault: not delegator");
        vault.withdraw(1);
    }

    function test_Withdraw_RevertAlreadyWithdrawn() public {
        // User1 delegates
        vm.startPrank(user1);
        usdc.approve(address(vault), 5000e6);
        vault.delegate(agentId, 5000e6);
        vm.stopPrank();

        // User1 withdraws
        vm.prank(user1);
        vault.withdraw(1);

        // User1 tries to withdraw again
        vm.prank(user1);
        vm.expectRevert("StrategyVault: already withdrawn");
        vault.withdraw(1);
    }
}
