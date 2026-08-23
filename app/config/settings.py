from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ATLAS"
    environment: str = "development"
    log_level: str = "INFO"
    workspace: str = "."
    artifact_dir: str = ".atlas/artifacts"
    database_url: str = "sqlite+aiosqlite:///./atlas.db"
    redis_url: str = "redis://localhost:6379/0"
    api_token: str | None = None

    default_provider: str = "openai"
    default_model: str = "gpt-5.4"
    openai_api_key: str | None = None

    max_iterations: int = 3
    max_agents_per_task: int = 8
    max_runtime_seconds: int = 900
    max_tool_calls: int = 50
    max_parallel_tasks: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ATLAS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
