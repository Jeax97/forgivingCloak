from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ENCRYPTION_KEY: str = "change-me-generate-a-fernet-key"

    # Database
    DATABASE_URL: str = "sqlite:///./data/forgivecloak.db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Have I Been Pwned
    HIBP_API_KEY: Optional[str] = None

    # Gmail OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Scanning
    MAX_PROBE_CONCURRENCY: int = 5
    IMAP_FETCH_DELAY: float = 0.5
    IMAP_MAX_EMAILS: int = 10000

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
