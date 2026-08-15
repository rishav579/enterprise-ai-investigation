"""Application configuration settings."""

from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Base repository root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    app_name: str = "Enterprise AI Investigation & Decision System"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Database configuration
    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT}/data/enterprise.db",
        description="SQLAlchemy database connection URL",
    )

    # Deterministic seed configuration
    random_seed: int = 42
    synthetic_customer_count: int = 500

    # CORS configuration (comma-separated origins)
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    # Static frontend directory override (optional)
    frontend_dist_dir: Optional[str] = None

    @property
    def allowed_cors_origins(self) -> list[str]:
        """Parse comma-separated cors_origins into a list of origins."""
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_prefix = "APP_"
        case_sensitive = False


settings = Settings()

