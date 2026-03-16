// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {TradeIntent} from "../src/trading/TradeIntent.sol";

contract TradeIntentTest is Test {
    TradeIntent public tradeIntent;

    uint256 internal signerPk = 0xA11CE;
    address internal signer;

    function setUp() public {
        tradeIntent = new TradeIntent();
        signer = vm.addr(signerPk);
    }

    function test_HashIntent() public view {
        TradeIntent.Intent memory intent = _createIntent();
        bytes32 hash = tradeIntent.hashIntent(intent);
        assertTrue(hash != bytes32(0));
    }

    function test_VerifyIntent() public view {
        TradeIntent.Intent memory intent = _createIntent();
        bytes32 digest = tradeIntent.hashIntent(intent);

        (uint8 v, bytes32 r, bytes32 s) = vm.sign(signerPk, digest);
        address recovered = tradeIntent.verifyIntent(intent, v, r, s);

        assertEq(recovered, signer);
    }

    function test_DifferentIntentsProduceDifferentHashes() public view {
        TradeIntent.Intent memory intent1 = _createIntent();
        TradeIntent.Intent memory intent2 = _createIntent();
        intent2.amountIn = 2 ether;

        bytes32 hash1 = tradeIntent.hashIntent(intent1);
        bytes32 hash2 = tradeIntent.hashIntent(intent2);

        assertTrue(hash1 != hash2);
    }

    function _createIntent() internal pure returns (TradeIntent.Intent memory) {
        return TradeIntent.Intent({
            agentId: 1,
            tokenIn: address(0xA),
            tokenOut: address(0xB),
            amountIn: 1 ether,
            minAmountOut: 0.95 ether,
            deadline: 1700000000,
            nonce: 0,
            strategyHash: keccak256("momentum_strategy")
        });
    }
}
