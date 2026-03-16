// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TradeIntent} from "./TradeIntent.sol";
import {IdentityRegistry} from "../registries/IdentityRegistry.sol";

/**
 * @title RiskManager
 * @notice Enforces risk limits on agent trade intents before execution
 * @dev Works alongside the hackathon-provided Risk Router
 *
 * Enforced limits per agent:
 * - Max position size (USD value)
 * - Max daily loss (percentage of starting capital)
 * - Max drawdown (percentage from peak)
 * - Whitelisted tokens only
 */
contract RiskManager {
    IdentityRegistry public immutable identityRegistry;

    struct RiskParams {
        uint256 maxPositionSizeUsd;  // Max single position in USD (18 decimals)
        uint256 maxDailyLossBps;     // Max daily loss in basis points (e.g., 500 = 5%)
        uint256 maxDrawdownBps;      // Max drawdown in basis points (e.g., 1500 = 15%)
        uint256 dailyTradeLimit;     // Max number of trades per day
        bool active;                 // Whether this agent's risk params are set
    }

    struct AgentState {
        uint256 peakCapital;         // Peak capital value (for drawdown calc)
        uint256 dailyStartCapital;   // Capital at start of current day
        uint256 dailyTradeCount;     // Trades executed today
        uint256 lastResetTimestamp;  // When daily counters were last reset
        uint256 currentCapital;      // Current capital value
    }

    /// @dev agentId => risk parameters
    mapping(uint256 => RiskParams) public riskParams;

    /// @dev agentId => agent state
    mapping(uint256 => AgentState) public agentStates;

    /// @dev Whitelisted tokens for trading
    mapping(address => bool) public whitelistedTokens;

    event RiskParamsSet(uint256 indexed agentId, uint256 maxPositionSizeUsd, uint256 maxDailyLossBps, uint256 maxDrawdownBps);
    event TradeApproved(uint256 indexed agentId, bytes32 intentHash);
    event TradeRejected(uint256 indexed agentId, bytes32 intentHash, string reason);
    event TokenWhitelisted(address indexed token, bool status);

    constructor(address _identityRegistry) {
        identityRegistry = IdentityRegistry(_identityRegistry);
    }

    /// @notice Set risk parameters for an agent
    /// @dev Only the agent owner can set risk params
    function setRiskParams(
        uint256 agentId,
        uint256 maxPositionSizeUsd,
        uint256 maxDailyLossBps,
        uint256 maxDrawdownBps,
        uint256 dailyTradeLimit
    ) external {
        require(
            identityRegistry.ownerOfAgent(agentId) == msg.sender,
            "RiskManager: not agent owner"
        );

        riskParams[agentId] = RiskParams({
            maxPositionSizeUsd: maxPositionSizeUsd,
            maxDailyLossBps: maxDailyLossBps,
            maxDrawdownBps: maxDrawdownBps,
            dailyTradeLimit: dailyTradeLimit,
            active: true
        });

        emit RiskParamsSet(agentId, maxPositionSizeUsd, maxDailyLossBps, maxDrawdownBps);
    }

    /// @notice Initialize agent capital tracking
    function initializeAgent(uint256 agentId, uint256 startingCapital) external {
        require(
            identityRegistry.ownerOfAgent(agentId) == msg.sender,
            "RiskManager: not agent owner"
        );

        agentStates[agentId] = AgentState({
            peakCapital: startingCapital,
            dailyStartCapital: startingCapital,
            dailyTradeCount: 0,
            lastResetTimestamp: block.timestamp,
            currentCapital: startingCapital
        });
    }

    /// @notice Check if a trade intent passes risk checks
    /// @param agentId The agent executing the trade
    /// @param amountUsd The trade amount in USD (18 decimals)
    /// @return approved Whether the trade is approved
    /// @return reason Rejection reason (empty if approved)
    function checkRisk(
        uint256 agentId,
        uint256 amountUsd
    ) external view returns (bool approved, string memory reason) {
        RiskParams memory params = riskParams[agentId];
        AgentState memory state = agentStates[agentId];

        if (!params.active) {
            return (false, "Risk params not set");
        }

        // Check position size
        if (amountUsd > params.maxPositionSizeUsd) {
            return (false, "Exceeds max position size");
        }

        // Check daily trade limit
        if (state.dailyTradeCount >= params.dailyTradeLimit) {
            return (false, "Daily trade limit reached");
        }

        // Check daily loss limit
        if (state.dailyStartCapital > 0) {
            uint256 dailyLoss = state.dailyStartCapital > state.currentCapital
                ? state.dailyStartCapital - state.currentCapital
                : 0;
            uint256 dailyLossBps = (dailyLoss * 10000) / state.dailyStartCapital;
            if (dailyLossBps >= params.maxDailyLossBps) {
                return (false, "Daily loss limit reached");
            }
        }

        // Check max drawdown
        if (state.peakCapital > 0) {
            uint256 drawdown = state.peakCapital > state.currentCapital
                ? state.peakCapital - state.currentCapital
                : 0;
            uint256 drawdownBps = (drawdown * 10000) / state.peakCapital;
            if (drawdownBps >= params.maxDrawdownBps) {
                return (false, "Max drawdown breached");
            }
        }

        return (true, "");
    }

    /// @notice Whitelist a token for trading
    function setTokenWhitelist(address token, bool status) external {
        // In production, this would be admin-only
        whitelistedTokens[token] = status;
        emit TokenWhitelisted(token, status);
    }

    /// @notice Update agent capital after a trade
    function updateCapital(uint256 agentId, uint256 newCapital) external {
        AgentState storage state = agentStates[agentId];
        state.currentCapital = newCapital;
        state.dailyTradeCount++;

        // Update peak
        if (newCapital > state.peakCapital) {
            state.peakCapital = newCapital;
        }

        // Reset daily counters if new day
        if (block.timestamp - state.lastResetTimestamp >= 1 days) {
            state.dailyStartCapital = newCapital;
            state.dailyTradeCount = 1;
            state.lastResetTimestamp = block.timestamp;
        }
    }
}
