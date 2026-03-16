"""
Execution Agent — On-chain trade execution and trust signal recording
The hands of ChronoTrader. Signs and submits trades, records validation artifacts.
"""

from crewai import Agent, Task
from langchain_openai import ChatOpenAI

from agent.tools import execute_swap, check_balance, register_agent, check_reputation


def create_execution_agent(openai_api_key: str, model: str = "gpt-4") -> Agent:
    """Create the Execution Agent — responsible for on-chain operations"""

    llm = ChatOpenAI(
        model=model,
        api_key=openai_api_key,
        temperature=0.0,  # Zero temp for deterministic execution
    )

    return Agent(
        role="Execution Specialist",
        goal=(
            "Execute approved trades on-chain with optimal timing and minimal slippage. "
            "Record all trade actions as validation artifacts on the ERC-8004 registries. "
            "Ensure every trade is auditable and contributes to the agent's on-chain reputation."
        ),
        backstory=(
            "You are a precision execution specialist with deep knowledge of DEX "
            "mechanics, MEV protection, and gas optimization. You handle the critical "
            "last mile — taking approved trade signals and turning them into successful "
            "on-chain transactions. You always verify transaction success, record "
            "validation data, and maintain a perfect audit trail."
        ),
        llm=llm,
        tools=[execute_swap, check_balance, register_agent, check_reputation],
        verbose=True,
        allow_delegation=False,
    )


def create_execution_task(
    agent: Agent,
    approved_trade: str,
    agent_id: int,
) -> Task:
    """Create a trade execution task"""

    return Task(
        description=(
            f"Execute the following approved trade on-chain:\n\n"
            f"APPROVED TRADE:\n{approved_trade}\n\n"
            f"AGENT ID: {agent_id}\n\n"
            f"EXECUTION STEPS:\n"
            f"1. Verify current token balances are sufficient\n"
            f"2. Check current prices haven't moved beyond acceptable range\n"
            f"3. Execute the swap via Uniswap V3\n"
            f"4. Verify the output amount meets minimum requirements\n"
            f"5. Record the trade as a validation artifact (hash trade data)\n"
            f"6. Log the execution result for reputation tracking\n\n"
            f"If any step fails, ABORT the trade and report the failure reason.\n"
            f"Never execute a trade if conditions have changed significantly from analysis."
        ),
        expected_output=(
            "A JSON execution report with: executed (bool), tx_hash, amount_in, "
            "amount_out, slippage_actual, gas_used, validation_hash, and any errors."
        ),
        agent=agent,
    )


def create_registration_task(
    agent: Agent,
    agent_card_uri: str,
) -> Task:
    """Create a task to register the agent on ERC-8004"""

    return Task(
        description=(
            f"Register ChronoTrader on the ERC-8004 Identity Registry.\n\n"
            f"Agent Card URI: {agent_card_uri}\n\n"
            f"Steps:\n"
            f"1. Register the agent using the provided URI\n"
            f"2. Verify the registration was successful\n"
            f"3. Return the assigned Agent ID\n"
            f"4. Confirm the agent card is accessible via the URI"
        ),
        expected_output=(
            "Agent ID and confirmation that registration is complete and verifiable."
        ),
        agent=agent,
    )
