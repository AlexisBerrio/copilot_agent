from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Única fuente de configuración del proceso. Nadie más lee variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Una clave desconocida en .env suele ser un typo (MONGO_URL por MONGO_URI): mejor fallar.
        extra="forbid",
        # Un salto de línea pegado al copiar un secreto rompe headers HTTP sin un error claro.
        str_strip_whitespace=True,
        frozen=True,
    )

    environment: Literal["local", "test", "ci", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # SecretStr: la URI puede llevar usuario y contraseña (Atlas).
    mongo_uri: SecretStr
    mongo_db_name: str = "copilot"


@lru_cache
def get_settings() -> Settings:
    return Settings()
