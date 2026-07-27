from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QuantProX"
    app_version: str = "1.0.0"
    environment: str = "local"
    debug: bool = False
    tenant_api_keys: dict[str, str] = {"demo": "dev-api-key"}
    session_secret: str = "local-development-session-secret"
    session_ttl_seconds: int = 28800
    session_secure_cookie: bool = False
    job_poll_interval_seconds: float = 1.0
    broker_provider: str = "sandbox"
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    database_url: str = (
        "postgresql+psycopg://quantprox:quantprox@localhost:5432/quantprox"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
