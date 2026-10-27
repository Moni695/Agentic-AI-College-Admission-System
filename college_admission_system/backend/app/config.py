from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:password@localhost:3306/college_admission"
    secret_key: str = "change-this-before-deployment"
    algorithm: str = "HS256"
    access_token_minutes: int = 480
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    application_fee: float = 500.0
    host: str = "0.0.0.0"
    port: int = 8000
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
