// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "lib/openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "lib/openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {IdentityRegistry} from "../registries/IdentityRegistry.sol";
import {RiskManager} from "./RiskManager.sol";

/**
 * @title StrategyVault
 * @notice Manages capital delegation for ChronoTrader agents
 * @dev Users delegate capital with enforced risk limits; agents trade within constraints
 */
contract StrategyVault {
    using SafeERC20 for IERC20;

    IdentityRegistry public immutable IDENTITY_REGISTRY;
    RiskManager public immutable RISK_MANAGER;

    /// @dev The stablecoin used for capital (e.g., USDC)
    IERC20 public immutable STABLECOIN;

    struct Delegation {
        address delegator;       // Who delegated the capital
        uint256 agentId;         // Which agent manages it
        uint256 amount;          // Amount delegated
        uint256 timestamp;       // When delegated
        bool active;             // Whether delegation is active
    }

    /// @dev delegationId => Delegation
    mapping(uint256 => Delegation) public delegations;
    uint256 public nextDelegationId = 1;

    /// @dev agentId => total capital under management
    mapping(uint256 => uint256) public agentCapital;

    event CapitalDelegated(uint256 indexed delegationId, address indexed delegator, uint256 indexed agentId, uint256 amount);
    event CapitalWithdrawn(uint256 indexed delegationId, address indexed delegator, uint256 amount);
    event TradeExecuted(uint256 indexed agentId, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);

    constructor(
        address _identityRegistry,
        address _riskManager,
        address _stablecoin
    ) {
        IDENTITY_REGISTRY = IdentityRegistry(_identityRegistry);
        RISK_MANAGER = RiskManager(_riskManager);
        STABLECOIN = IERC20(_stablecoin);
    }

    /// @notice Delegate capital to an agent
    /// @param agentId The agent to delegate to
    /// @param amount The amount of stablecoin to delegate
    function delegate(uint256 agentId, uint256 amount) external {
        require(amount > 0, "StrategyVault: zero amount");
        require(
            IDENTITY_REGISTRY.ownerOfAgent(agentId) != address(0),
            "StrategyVault: agent not registered"
        );

        STABLECOIN.safeTransferFrom(msg.sender, address(this), amount);

        uint256 delegationId = nextDelegationId++;
        delegations[delegationId] = Delegation({
            delegator: msg.sender,
            agentId: agentId,
            amount: amount,
            timestamp: block.timestamp,
            active: true
        });

        agentCapital[agentId] += amount;

        emit CapitalDelegated(delegationId, msg.sender, agentId, amount);
    }

    /// @notice Withdraw delegated capital
    /// @param delegationId The delegation to withdraw
    function withdraw(uint256 delegationId) external {
        Delegation storage d = delegations[delegationId];
        require(d.delegator == msg.sender, "StrategyVault: not delegator");
        require(d.active, "StrategyVault: already withdrawn");

        d.active = false;
        agentCapital[d.agentId] -= d.amount;

        STABLECOIN.safeTransfer(msg.sender, d.amount);

        emit CapitalWithdrawn(delegationId, msg.sender, d.amount);
    }

    /// @notice Get total capital managed by an agent
    function getAgentCapital(uint256 agentId) external view returns (uint256) {
        return agentCapital[agentId];
    }
}
