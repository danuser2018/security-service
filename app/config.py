import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "security-service"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    SECURITY_HMAC_SECRET: str = os.getenv("SECURITY_HMAC_SECRET", "dev-secret-key-change-in-prod")
    TOKEN_TTL_SECONDS: int = 300

    class Config:
        env_file = ".env"

settings = Settings()
