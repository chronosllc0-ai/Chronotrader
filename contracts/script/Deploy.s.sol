// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {IdentityRegistry} from "../src/registries/IdentityRegistry.sol";
import {ReputationRegistry} from "../src/registries/ReputationRegistry.sol";
import {ValidationRegistry} from "../src/registries/ValidationRegistry.sol";
import {TradeIntent} from "../src/trading/TradeIntent.sol";
import {RiskManager} from "../src/trading/RiskManager.sol";
import {StrategyVault} from "../src/trading/StrategyVault.sol";

contract Deploy is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("AGENT_PRIVATE_KEY");
        address stablecoin = vm.envAddress("STABLECOIN_ADDRESS");

        vm.startBroadcast(deployerPrivateKey);

        IdentityRegistry identityRegistry = new IdentityRegistry();
        ReputationRegistry reputationRegistry = new ReputationRegistry(address(identityRegistry));
        ValidationRegistry validationRegistry = new ValidationRegistry(address(identityRegistry));
        TradeIntent tradeIntent = new TradeIntent();
        RiskManager riskManager = new RiskManager(address(identityRegistry));
        StrategyVault strategyVault = new StrategyVault(address(identityRegistry), address(riskManager), stablecoin);

        vm.stopBroadcast();

        console.log("IdentityRegistry:", address(identityRegistry));
        console.log("ReputationRegistry:", address(reputationRegistry));
        console.log("ValidationRegistry:", address(validationRegistry));
        console.log("TradeIntent:", address(tradeIntent));
        console.log("RiskManager:", address(riskManager));
        console.log("StrategyVault:", address(strategyVault));

        string memory root = vm.projectRoot();
        string memory path = string.concat(root, "/deployed_addresses.json");
        string memory json = "deployment";
        vm.serializeAddress(json, "identity_registry", address(identityRegistry));
        vm.serializeAddress(json, "reputation_registry", address(reputationRegistry));
        vm.serializeAddress(json, "validation_registry", address(validationRegistry));
        vm.serializeAddress(json, "trade_intent", address(tradeIntent));
        vm.serializeAddress(json, "risk_manager", address(riskManager));
        string memory finalJson = vm.serializeAddress(json, "strategy_vault", address(strategyVault));
        vm.writeJson(finalJson, path);
    }
}
