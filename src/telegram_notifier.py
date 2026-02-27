import logging
import time
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# Telegram rate limit: ~30 messages/second to different chats,
# but only 1 message/second to the same chat.
_MIN_SEND_INTERVAL = 1.1  # seconds between messages to the same chat


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self._api_url = _TELEGRAM_API.format(token=bot_token)
        self._last_send_time: float = 0.0

    def send_article(
        self,
        title: str,
        url: str,
        matched_keywords: list[str],
        feed_url: str,
        published: str | None = None,
    ) -> bool:
        source = urlparse(feed_url).netloc or feed_url
        keywords_str = ", ".join(matched_keywords[:5])

        date_line = ""
        if published:
            date_line = f"📅 {_escape_html(published)}\n"

        message = (
            f"📰 <b>{_escape_html(title)}</b>\n\n"
            f"{date_line}"
            f"🏷 <i>{_escape_html(keywords_str)}</i>\n"
            f"🌐 {_escape_html(source)}\n\n"
            f'<a href="{url}">Read article →</a>'
        )

        return self._send(message)

    def _send(self, text: str) -> bool:
        # Respect Telegram rate limits.
        elapsed = time.time() - self._last_send_time
        if elapsed < _MIN_SEND_INTERVAL:
            time.sleep(_MIN_SEND_INTERVAL - elapsed)

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            resp = requests.post(self._api_url, json=payload, timeout=self.timeout)
            self._last_send_time = time.time()

            if resp.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True

            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                logger.warning("Rate limited by Telegram. Retrying after %ds", retry_after)
                time.sleep(retry_after)
                return self._send(text)

            logger.error(
                "Telegram API error %d: %s", resp.status_code, resp.text[:200]
            )
            return False

        except requests.RequestException:
            logger.exception("Failed to send Telegram message")
            return False


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
