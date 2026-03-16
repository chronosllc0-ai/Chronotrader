// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {ReputationRegistry} from "../src/registries/ReputationRegistry.sol";
import {ValidationRegistry} from "../src/registries/ValidationRegistry.sol";
import {TradeIntent} from "../src/trading/TradeIntent.sol";
import {RiskManager} from "../src/trading/RiskManager.sol";

/**
 * @title Deploy
 * @notice Deploys all ChronoTrader contracts
 * @dev Run: forge script script/Deploy.s.sol --rpc-url $RPC_URL --broadcast
 */
contract Deploy is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("AGENT_PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy ERC-8004 Registries
        IdentityRegistry identityRegistry = new IdentityRegistry();
        console.log("IdentityRegistry:", address(identityRegistry));

        ReputationRegistry reputationRegistry = new ReputationRegistry(address(identityRegistry));
        console.log("ReputationRegistry:", address(reputationRegistry));

        ValidationRegistry validationRegistry = new ValidationRegistry(address(identityRegistry));
        console.log("ValidationRegistry:", address(validationRegistry));

        // 2. Deploy Trading Contracts
        TradeIntent tradeIntent = new TradeIntent();
        console.log("TradeIntent:", address(tradeIntent));

        RiskManager riskManager = new RiskManager(address(identityRegistry));
        console.log("RiskManager:", address(riskManager));

        // Note: StrategyVault requires a stablecoin address
        // Deploy separately after configuring stablecoin for the target network
        // StrategyVault vault = new StrategyVault(
        //     address(identityRegistry),
        //     address(riskManager),
        //     STABLECOIN_ADDRESS
        // );

        vm.stopBroadcast();

        // Output addresses for .env
        console.log("\n--- Copy to .env ---");
        console.log("IDENTITY_REGISTRY_ADDRESS=", address(identityRegistry));
        console.log("REPUTATION_REGISTRY_ADDRESS=", address(reputationRegistry));
        console.log("VALIDATION_REGISTRY_ADDRESS=", address(validationRegistry));
        console.log("TRADE_INTENT_ADDRESS=", address(tradeIntent));
        console.log("RISK_MANAGER_ADDRESS=", address(riskManager));
    }
}
