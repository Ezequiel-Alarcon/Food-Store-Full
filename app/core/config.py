from typing import Optional, Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DATABASE_URL: Optional[str] = None

    # ── Postgres individual fields (alternative to DATABASE_URL) ──────────────
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[str] = None

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # ─── Logging ─────────────────────────────────────────────────────────────
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


    # ─── Rate Limiting ───────────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 60
    RATE_LIMIT_DEFAULT_BURST: int = 10
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_AUTH_BURST: int = 5

    @property
    def rate_limit_default_burst(self) -> int:
        return self.RATE_LIMIT_DEFAULT_BURST

    @property
    def rate_limit_default_per_minute(self) -> int:
        return self.RATE_LIMIT_DEFAULT_PER_MINUTE

    @property
    def rate_limit_auth_burst(self) -> int:
        return self.RATE_LIMIT_AUTH_BURST

    @property
    def rate_limit_auth_per_minute(self) -> int:
        return self.RATE_LIMIT_AUTH_PER_MINUTE
    
    CLOUDINARY_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # --- MercadoPago ---
    MP_ACCESS_TOKEN: Optional[str] = None
    MP_PUBLIC_KEY: Optional[str] = None
    MP_WEBHOOK_URL: Optional[str] = None
    NGROK_URL: Optional[str] = None
    
    # --- CORS y Frontend ---
    CORS_ORIGINS: str = "http://localhost:5173"
    VITE_FRONTEND_URL: str = "http://localhost:5173"
    VITE_API_URL: str = "http://localhost:8000"

    @model_validator(mode="after")
    def fix_database_url(self):
        if not self.DATABASE_URL and all([
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            self.POSTGRES_DB,
        ]):
            host = self.POSTGRES_HOST or "localhost"
            port = self.POSTGRES_PORT or "5432"
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{host}:{port}/{self.POSTGRES_DB}"
            )

        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow" 
    )

settings = Settings()