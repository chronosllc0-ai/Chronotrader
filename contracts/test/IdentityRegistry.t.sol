// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";

contract IdentityRegistryTest is Test {
    IdentityRegistry public registry;
    address public agent1 = address(0x1);
    address public agent2 = address(0x2);

    function setUp() public {
        registry = new IdentityRegistry();
    }

    function test_Register() public {
        vm.prank(agent1);
        uint256 agentId = registry.register("ipfs://QmAgentCard1");

        assertEq(agentId, 1);
        assertEq(registry.ownerOfAgent(1), agent1);
        assertEq(registry.agentCount(), 1);
    }

    function test_RegisterMultiple() public {
        vm.prank(agent1);
        uint256 id1 = registry.register("ipfs://QmAgentCard1");

        vm.prank(agent2);
        uint256 id2 = registry.register("ipfs://QmAgentCard2");

        assertEq(id1, 1);
        assertEq(id2, 2);
        assertEq(registry.agentCount(), 2);
    }

    function test_UpdateURI() public {
        vm.prank(agent1);
        registry.register("ipfs://QmOldCard");

        vm.prank(agent1);
        registry.updateURI(1, "ipfs://QmNewCard");

        assertEq(registry.tokenURI(1), "ipfs://QmNewCard");
    }

    function test_UpdateURI_RevertNotOwner() public {
        vm.prank(agent1);
        registry.register("ipfs://QmAgentCard");

        vm.prank(agent2);
        vm.expectRevert("IdentityRegistry: not owner");
        registry.updateURI(1, "ipfs://QmHackerCard");
    }


    function test_Register_FromZeroAddressReverts() public {
        vm.prank(address(0));
        vm.expectRevert();
        registry.register("ipfs://QmZero");
    }

    function test_SetAgentWallet() public {
        vm.prank(agent1);
        registry.register("ipfs://QmAgentCard");

        address newWallet = address(0x3);
        vm.prank(agent1);
        registry.setAgentWallet(1, newWallet);

        assertEq(registry.agentWallets(1), newWallet);
    }
}
