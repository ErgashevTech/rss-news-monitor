import os
import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ArticleStorage:
    def __init__(self, db_path: str):
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()
        logger.info("Storage initialized at %s", db_path)

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                feed_url TEXT,
                matched_keywords TEXT,
                processed_at TEXT NOT NULL
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url ON processed_articles(url)
        """)
        self.conn.commit()

    def is_processed(self, url: str) -> bool:
        cursor = self.conn.execute(
            "SELECT 1 FROM processed_articles WHERE url = ?", (url,)
        )
        return cursor.fetchone() is not None

    def mark_processed(
        self,
        url: str,
        title: str,
        feed_url: str,
        matched_keywords: list[str] | None = None,
    ):
        self.conn.execute(
            """INSERT OR IGNORE INTO processed_articles
               (url, title, feed_url, matched_keywords, processed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                url,
                title,
                feed_url,
                ", ".join(matched_keywords) if matched_keywords else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def get_stats(self) -> dict:
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_articles")
        total = cursor.fetchone()[0]
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM processed_articles WHERE matched_keywords IS NOT NULL"
        )
        relevant = cursor.fetchone()[0]
        return {"total_processed": total, "relevant_sent": relevant}

    def close(self):
        self.conn.close()
        logger.info("Storage closed")
