from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_ENV_CANDIDATES = (_BACKEND_DIR / ".env", _REPO_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(path) for path in _ENV_CANDIDATES),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    postgres_user: str = "escribania"
    postgres_password: str = "escribania"
    postgres_db: str = "escribania_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_hours: int = 8
    cors_origins: str = "http://localhost:5173"

    # Dollar exchange rate API — ArgentinaDatos as primary, DolarAPI as fallback
    cotizacion_api_url: str = "https://api.argentinadatos.com/v1/cotizaciones/dolares"
    cotizacion_fallback_url: str = "https://dolarapi.com/v1/dolares"
    cotizacion_cache_ttl_hours: int = 8
    cotizacion_ssl_verify: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
