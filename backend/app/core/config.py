import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "ZFlow API"
    environment: str = os.getenv("APP_ENV", "local")
    log_level: str = os.getenv("LOG_LEVEL", "info")


settings = Settings()
