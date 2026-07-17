"""Application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"
    database_url: str = "sqlite:///./libresim.db"
    cors_origins: str = "http://localhost:4200"

    # Simulation settings
    max_simulation_time: float = 1000.0
    default_step_size: float = 0.01
    max_steps: int = 1000000
    max_retained_simulation_sessions: int = Field(default=8, ge=1)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
