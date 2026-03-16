"""
ChronoTrader Agent Configuration
Loads settings from .env file and provides typed access
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ── OpenAI ──────────────────────────────────────────────────────────
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")

    # ── Blockchain ──────────────────────────────────────────────────────
    agent_private_key: str = Field(..., env="AGENT_PRIVATE_KEY")
    base_sepolia_rpc_url: str = Field(
        default="https://sepolia.base.org", env="BASE_SEPOLIA_RPC_URL"
    )
    local_rpc_url: str = Field(
        default="http://localhost:8545", env="LOCAL_RPC_URL"
    )
    network: str = Field(default="local", env="NETWORK")

    # ── Contract Addresses ──────────────────────────────────────────────
    identity_registry_address: Optional[str] = Field(
        default=None, env="IDENTITY_REGISTRY_ADDRESS"
    )
    reputation_registry_address: Optional[str] = Field(
        default=None, env="REPUTATION_REGISTRY_ADDRESS"
    )
    validation_registry_address: Optional[str] = Field(
        default=None, env="VALIDATION_REGISTRY_ADDRESS"
    )
    risk_router_address: Optional[str] = Field(
        default=None, env="RISK_ROUTER_ADDRESS"
    )
    strategy_vault_address: Optional[str] = Field(
        default=None, env="STRATEGY_VAULT_ADDRESS"
    )

    # ── Hackathon Sandbox ───────────────────────────────────────────────
    sandbox_vault_address: Optional[str] = Field(
        default=None, env="SANDBOX_VAULT_ADDRESS"
    )
    sandbox_risk_router_address: Optional[str] = Field(
        default=None, env="SANDBOX_RISK_ROUTER_ADDRESS"
    )

    # ── Agent Configuration ─────────────────────────────────────────────
    agent_name: str = Field(default="ChronoTrader", env="AGENT_NAME")
    agent_description: str = Field(
        default="Autonomous AI trading agent with ERC-8004 trust",
        env="AGENT_DESCRIPTION",
    )
    max_position_size_usd: float = Field(
        default=1000.0, env="MAX_POSITION_SIZE_USD"
    )
    max_daily_loss_pct: float = Field(default=5.0, env="MAX_DAILY_LOSS_PCT")
    max_drawdown_pct: float = Field(default=15.0, env="MAX_DRAWDOWN_PCT")
    default_strategy: str = Field(default="momentum", env="DEFAULT_STRATEGY")

    # ── IPFS ────────────────────────────────────────────────────────────
    ipfs_gateway: str = Field(
        default="https://ipfs.io/ipfs/", env="IPFS_GATEWAY"
    )

    @property
    def rpc_url(self) -> str:
        """Get the active RPC URL based on network setting"""
        if self.network == "local":
            return self.local_rpc_url
        elif self.network == "base_sepolia":
            return self.base_sepolia_rpc_url
        else:
            return self.base_sepolia_rpc_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
settings = Settings()
