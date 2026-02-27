import logging
from dataclasses import dataclass

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    link: str
    summary: str
    feed_url: str
    published: str | None = None


class RSSFetcher:
    def __init__(self, feed_urls: list[str], timeout: int = 30):
        self.feed_urls = feed_urls
        self.timeout = timeout

    def fetch_all(self) -> list[Article]:
        articles: list[Article] = []
        for url in self.feed_urls:
            try:
                fetched = self._fetch_feed(url)
                articles.extend(fetched)
            except Exception:
                logger.exception("Failed to fetch feed: %s", url)
        logger.info("Fetched %d total articles from %d feeds", len(articles), len(self.feed_urls))
        return articles

    def _fetch_feed(self, url: str) -> list[Article]:
        feed = feedparser.parse(url, request_headers={"User-Agent": "NewsMonitor/1.0"})

        if feed.bozo and not feed.entries:
            logger.warning("Feed parse error for %s: %s", url, feed.bozo_exception)
            return []

        articles: list[Article] = []
        for entry in feed.entries:
            link = entry.get("link", "").strip()
            if not link:
                continue

            article = Article(
                title=entry.get("title", "No title").strip(),
                link=link,
                summary=entry.get("summary", entry.get("description", "")).strip(),
                feed_url=url,
                published=entry.get("published"),
            )
            articles.append(article)

        logger.debug("Fetched %d articles from %s", len(articles), url)
        return articles
