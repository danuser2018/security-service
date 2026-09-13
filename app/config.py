import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "security-service"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    SECURITY_HMAC_SECRET: str = os.getenv("SECURITY_HMAC_SECRET", "dev-secret-key-change-in-prod")
    TOKEN_TTL_SECONDS: int = 300
    NATS_URL: str = "nats://nats:4222"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
