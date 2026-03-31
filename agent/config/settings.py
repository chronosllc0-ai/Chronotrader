"""ChronoTrader agent configuration."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")

    # Chain
    agent_private_key: str = Field(default="", env="AGENT_PRIVATE_KEY")
    base_sepolia_rpc_url: str = Field(default="https://sepolia.base.org", env="BASE_SEPOLIA_RPC_URL")
    local_rpc_url: str = Field(default="http://localhost:8545", env="LOCAL_RPC_URL")
    network: str = Field(default="local", env="NETWORK")

    # Contracts
    identity_registry_address: Optional[str] = Field(default=None, env="IDENTITY_REGISTRY_ADDRESS")
    reputation_registry_address: Optional[str] = Field(default=None, env="REPUTATION_REGISTRY_ADDRESS")
    validation_registry_address: Optional[str] = Field(default=None, env="VALIDATION_REGISTRY_ADDRESS")
    risk_router_address: Optional[str] = Field(default=None, env="RISK_ROUTER_ADDRESS")
    strategy_vault_address: Optional[str] = Field(default=None, env="STRATEGY_VAULT_ADDRESS")
    trade_intent_address: Optional[str] = Field(default=None, env="TRADE_INTENT_ADDRESS")

    # Sandbox
    sandbox_vault_address: Optional[str] = Field(default=None, env="SANDBOX_VAULT_ADDRESS")
    sandbox_risk_router_address: Optional[str] = Field(default=None, env="SANDBOX_RISK_ROUTER_ADDRESS")

    # Agent
    agent_name: str = Field(default="ChronoTrader", env="AGENT_NAME")
    agent_description: str = Field(default="Autonomous AI trading agent with ERC-8004 trust", env="AGENT_DESCRIPTION")
    max_position_size_usd: float = Field(default=1000.0, env="MAX_POSITION_SIZE_USD")
    max_daily_loss_pct: float = Field(default=5.0, env="MAX_DAILY_LOSS_PCT")
    max_drawdown_pct: float = Field(default=15.0, env="MAX_DRAWDOWN_PCT")
    default_strategy: str = Field(default="momentum", env="DEFAULT_STRATEGY")
    simulation_mode: bool = Field(default=True, env="SIMULATION_MODE")
    loop_interval_seconds: int = Field(default=900, env="LOOP_INTERVAL_SECONDS")
    agent_id: int = Field(default=1, env="AGENT_ID")

    # IPFS
    ipfs_gateway: str = Field(default="https://gateway.pinata.cloud/ipfs/", env="IPFS_GATEWAY")
    agent_card_ipfs_uri: str = Field(default="", env="AGENT_CARD_IPFS_URI")

    @property
    def rpc_url(self) -> str:
        return self.local_rpc_url if self.network == "local" else self.base_sepolia_rpc_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
