# app/core/config.py
# Centralised settings loaded from environment / .env file.
# All secrets stay out of source code.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------
    APP_NAME: str = "Online Voting System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # -----------------------------------------------------------------------
    # Database — aiomysql async driver
    # Format: mysql+aiomysql://user:pass@host:port/dbname
    # -----------------------------------------------------------------------
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "voting_db"
    DB_ECHO: bool = False           # set True locally to log all SQL

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # -----------------------------------------------------------------------
    # Security — JWT
    # -----------------------------------------------------------------------
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_openssl_rand_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # -----------------------------------------------------------------------
    # CORS — tighten in production
    # -----------------------------------------------------------------------
    ALLOWED_ORIGINS: list[str] = ["http://localhost", "http://127.0.0.1"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton — import this everywhere instead of instantiating again
settings = Settings()
