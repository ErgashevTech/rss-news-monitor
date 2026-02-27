import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config import (
    CHECK_INTERVAL_MINUTES,
    DB_PATH,
    LOG_LEVEL,
    REQUEST_TIMEOUT,
    RSS_FEEDS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from src.relevance_checker import RelevanceChecker
from src.rss_fetcher import RSSFetcher
from src.storage import ArticleStorage
from src.telegram_notifier import TelegramNotifier

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news-monitor")

# Silence noisy third-party loggers.
logging.getLogger("apscheduler").setLevel(logging.WARNING)

storage = ArticleStorage(DB_PATH)
fetcher = RSSFetcher(RSS_FEEDS, timeout=REQUEST_TIMEOUT)
checker = RelevanceChecker()
notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, timeout=REQUEST_TIMEOUT)


def check_feeds():
    logger.info("--- Feed check started ---")
    articles = fetcher.fetch_all()

    new_count = 0
    relevant_count = 0
    sent_count = 0

    for article in articles:
        if storage.is_processed(article.link):
            continue

        new_count += 1
        is_relevant, matched = checker.check(article.title, article.summary)

        if is_relevant:
            relevant_count += 1
            success = notifier.send_article(
                title=article.title,
                url=article.link,
                matched_keywords=matched,
                feed_url=article.feed_url,
                published=article.published,
            )
            if success:
                sent_count += 1
                storage.mark_processed(
                    url=article.link,
                    title=article.title,
                    feed_url=article.feed_url,
                    matched_keywords=matched,
                )
            else:
                logger.error("Failed to send article, will retry next cycle: %s", article.link)
        else:
            # Mark irrelevant articles as processed too (without keywords)
            # so we don't re-check them every cycle.
            storage.mark_processed(
                url=article.link,
                title=article.title,
                feed_url=article.feed_url,
            )

    stats = storage.get_stats()
    logger.info(
        "--- Feed check complete: %d new, %d relevant, %d sent | DB total: %d processed, %d relevant ---",
        new_count,
        relevant_count,
        sent_count,
        stats["total_processed"],
        stats["relevant_sent"],
    )


def shutdown(signum, _frame):
    sig_name = signal.Signals(signum).name
    logger.info("Received %s, shutting down...", sig_name)
    storage.close()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("News Monitor starting")
    logger.info("Monitoring %d feeds every %d minutes", len(RSS_FEEDS), CHECK_INTERVAL_MINUTES)
    logger.info("Feeds: %s", RSS_FEEDS)

    # Run first check immediately on startup.
    check_feeds()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        check_feeds,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="feed_checker",
        max_instances=1,
        coalesce=True,
    )

    logger.info("Scheduler started. Next check in %d minutes.", CHECK_INTERVAL_MINUTES)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
    finally:
        storage.close()


if __name__ == "__main__":
    main()
