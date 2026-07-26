from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QuantProX"
    app_version: str = "1.0.0-beta.2"
    environment: str = "local"
    debug: bool = False
    tenant_api_keys: dict[str, str] = {"demo": "dev-api-key"}
    database_url: str = (
        "postgresql+psycopg://quantprox:quantprox@localhost:5432/quantprox"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
