"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    environment: str = "development"
    database_url: str = "sqlite:///./libresim.db"
    cors_origins: list[str] = ["http://localhost:4200"]

    # Simulation settings
    max_simulation_time: float = 1000.0
    default_step_size: float = 0.01
    max_steps: int = 1000000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
