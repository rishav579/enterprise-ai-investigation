"""Application configuration settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

# Base repository root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    app_name: str = "Enterprise AI Investigation & Decision System"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database configuration
    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT}/data/enterprise.db",
        description="SQLAlchemy database connection URL",
    )

    # Deterministic seed configuration
    random_seed: int = 42
    synthetic_customer_count: int = 500

    class Config:
        env_prefix = "APP_"
        case_sensitive = False


settings = Settings()
