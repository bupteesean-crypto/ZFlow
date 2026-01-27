# app/db/init_db.py

import logging
from dotenv import load_dotenv

load_dotenv()

from app.db.base import Base
from app.db.session import engine
from app.db import models  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("init_db")


def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Done.")


if __name__ == "__main__":
    init_db()
