"""
Risk Agent — Position sizing, stop-loss management, and drawdown protection
The guardian of ChronoTrader. Ensures all trades pass risk checks before execution.
"""

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agent.tools import get_token_price, check_balance


def create_risk_agent(openai_api_key: str, model: str = "gpt-4") -> Agent:
    """Create the Risk Agent — responsible for risk management and trade validation"""

    llm = ChatOpenAI(
        model=model,
        api_key=openai_api_key,
        temperature=0.0,  # Zero temp for deterministic risk checks
    )

    return Agent(
        role="Chief Risk Officer",
        goal=(
            "Validate every trade signal against strict risk parameters before "
            "allowing execution. Protect capital at all costs. Never allow a trade "
            "that could breach drawdown limits or expose the portfolio to excessive risk."
        ),
        backstory=(
            "You are a battle-tested risk manager who has survived multiple market "
            "crashes. Your #1 rule: capital preservation comes before profit. You've "
            "seen traders blow up accounts from overleveraging and ignoring stop-losses. "
            "You enforce position limits ruthlessly and have never allowed a max drawdown "
            "breach on your watch. You check: position size, correlation risk, liquidity "
            "depth, slippage estimates, and portfolio concentration."
        ),
        llm=llm,
        tools=[get_token_price, check_balance],
        verbose=True,
        allow_delegation=False,
    )


def create_risk_check_task(
    agent: Agent,
    trade_signal: str,
    current_capital: float,
    max_position_pct: float = 20.0,
    max_daily_loss_pct: float = 5.0,
    max_drawdown_pct: float = 15.0,
) -> Task:
    """Create a risk validation task for a proposed trade"""

    return Task(
        description=(
            f"Validate the following trade signal against risk parameters:\n\n"
            f"TRADE SIGNAL:\n{trade_signal}\n\n"
            f"RISK PARAMETERS:\n"
            f"- Current capital: ${current_capital:,.2f}\n"
            f"- Max position size: {max_position_pct}% of capital "
            f"(${current_capital * max_position_pct / 100:,.2f})\n"
            f"- Max daily loss: {max_daily_loss_pct}% "
            f"(${current_capital * max_daily_loss_pct / 100:,.2f})\n"
            f"- Max drawdown: {max_drawdown_pct}%\n"
            f"- Min risk/reward ratio: 2:1\n"
            f"- Max slippage tolerance: 1%\n\n"
            f"VALIDATION CHECKLIST:\n"
            f"1. Does position size comply with limits?\n"
            f"2. Is stop-loss properly set and within acceptable range?\n"
            f"3. Is risk/reward ratio >= 2:1?\n"
            f"4. Does the trade have sufficient liquidity?\n"
            f"5. Would this trade breach daily loss limits if stopped out?\n"
            f"6. Would this trade breach max drawdown if stopped out?\n"
            f"7. Is portfolio concentration acceptable?\n\n"
            f"Return APPROVED or REJECTED with detailed reasoning."
        ),
        expected_output=(
            "A JSON object with: approved (bool), adjusted_position_size (if needed), "
            "risk_score (1-10, lower is safer), warnings (list), and reasoning (string)."
        ),
        agent=agent,
    )
