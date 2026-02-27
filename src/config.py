import os
import sys
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        logger.critical("Missing required environment variable: %s", name)
        sys.exit(1)
    return value


TELEGRAM_BOT_TOKEN: str = _require_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = _require_env("TELEGRAM_CHAT_ID")

RSS_FEEDS: list[str] = [
    url.strip()
    for url in os.environ.get("RSS_FEEDS", "").split(",")
    if url.strip()
]

if not RSS_FEEDS:
    logger.critical("RSS_FEEDS is empty. Provide comma-separated feed URLs.")
    sys.exit(1)

CHECK_INTERVAL_MINUTES: int = int(os.environ.get("CHECK_INTERVAL_MINUTES", "15"))
DB_PATH: str = os.environ.get("DB_PATH", "data/articles.db")
REQUEST_TIMEOUT: int = int(os.environ.get("REQUEST_TIMEOUT", "30"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
