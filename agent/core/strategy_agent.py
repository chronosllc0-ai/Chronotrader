"""
Strategy Agent — LLM-powered market analysis and trade decision-making
The brain of ChronoTrader. Analyzes market conditions and generates trade signals.
"""

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agent.tools import get_token_price, get_market_summary, check_reputation


def create_strategy_agent(openai_api_key: str, model: str = "gpt-4") -> Agent:
    """Create the Strategy Agent — responsible for market analysis and trade signals"""

    llm = ChatOpenAI(
        model=model,
        api_key=openai_api_key,
        temperature=0.1,  # Low temp for consistent analysis
    )

    return Agent(
        role="Senior Trading Strategist",
        goal=(
            "Analyze market conditions and generate high-conviction trade signals "
            "with clear entry/exit points, position sizing recommendations, and "
            "risk/reward ratios. Optimize for risk-adjusted returns (Sharpe ratio) "
            "not raw PnL."
        ),
        backstory=(
            "You are an elite quantitative trading strategist with 15 years of "
            "experience in DeFi and traditional markets. You specialize in momentum "
            "strategies, mean reversion, and yield optimization. You never chase "
            "trades — you wait for high-probability setups with favorable risk/reward. "
            "Your track record shows consistent risk-adjusted returns with max "
            "drawdowns under 15%."
        ),
        llm=llm,
        tools=[get_token_price, get_market_summary, check_reputation],
        verbose=True,
        allow_delegation=False,
    )


def create_market_analysis_task(agent: Agent, market_context: str = "") -> Task:
    """Create a market analysis task for the Strategy Agent"""

    return Task(
        description=(
            f"Perform a comprehensive market analysis for the current trading session.\n\n"
            f"Additional context: {market_context}\n\n"
            f"Your analysis MUST include:\n"
            f"1. Current price levels for key assets (ETH, BTC)\n"
            f"2. Trend assessment (bullish/bearish/neutral) with confidence level\n"
            f"3. Key support and resistance levels\n"
            f"4. Volume and liquidity assessment\n"
            f"5. Risk factors and potential catalysts\n"
            f"6. Recommended action: BUY / SELL / HOLD with specific parameters\n\n"
            f"If recommending a trade:\n"
            f"- Entry price range\n"
            f"- Stop-loss level (max 3% from entry)\n"
            f"- Take-profit target(s)\n"
            f"- Position size as % of capital (never exceed 20%)\n"
            f"- Risk/reward ratio (minimum 2:1)\n"
            f"- Confidence level (1-10)\n\n"
            f"Be conservative. No trade is better than a bad trade."
        ),
        expected_output=(
            "A structured JSON analysis with: trend_assessment, confidence_level, "
            "recommended_action (BUY/SELL/HOLD), entry_price, stop_loss, "
            "take_profit, position_size_pct, risk_reward_ratio, and rationale."
        ),
        agent=agent,
    )


def create_trade_signal_task(agent: Agent, analysis: str) -> Task:
    """Create a specific trade signal task based on market analysis"""

    return Task(
        description=(
            f"Based on the following market analysis, generate a specific trade signal:\n\n"
            f"{analysis}\n\n"
            f"Generate an EIP-712 compatible TradeIntent with:\n"
            f"- tokenIn: address of token to sell\n"
            f"- tokenOut: address of token to buy\n"
            f"- amountIn: exact amount to trade\n"
            f"- minAmountOut: minimum acceptable output (include 0.5% slippage)\n"
            f"- deadline: 30 minutes from now\n"
            f"- strategyHash: hash of the analysis rationale\n\n"
            f"Also provide a human-readable summary of the trade rationale."
        ),
        expected_output=(
            "A TradeIntent JSON object ready for EIP-712 signing, plus a "
            "human-readable trade rationale string."
        ),
        agent=agent,
    )
