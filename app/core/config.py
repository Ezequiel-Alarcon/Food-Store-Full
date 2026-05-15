from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None

    # Configuración para cargar variables de entorno desde un archivo .env
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Validador para corregir el formato de DATABASE_URL si es necesario
    @model_validator(mode="after")
    def fix_database_url(self) -> "Settings":
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        return self


settings = Settings()