import logging

from app.core.config import settings


def setup_logging() -> None:
    # Centralized logging configuration for the API service.
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
