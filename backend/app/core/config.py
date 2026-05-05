from functools import lru_cache
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str

    # Gemini
    gemini_api_key: str

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_db_url: str
    supabase_db_url_admin: str | None = None
    mkt_app_db_password: str

    # Auth
    auth_bypass: bool = False
    dev_tenant_id: UUID = Field(default=UUID("00000000-0000-0000-0000-000000000001"))
    dev_user_id: UUID = Field(default=UUID("00000000-0000-0000-0000-000000000002"))

    # App
    app_env: str = "development"
    app_port: int = 3002
    frontend_url: str = "http://localhost:5173"

    # Models
    anthropic_model_orchestrator: str = "claude-sonnet-4-6"
    anthropic_model_content: str = "claude-sonnet-4-6"
    anthropic_model_brand: str = "claude-haiku-4-5-20251001"
    gemini_model_image: str = "gemini-3.1-flash-image-preview"


@lru_cache
def get_settings() -> Settings:
    return Settings()
