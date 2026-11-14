"""Small SQLite-backed feedback store for the учебный deployment."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class FeedbackStore:
    """Persist operator feedback and provide request-id idempotency."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    request_id TEXT PRIMARY KEY,
                    correct_topic TEXT,
                    comment TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def accept(
        self,
        request_id: str,
        correct_topic: str | None = None,
        comment: str | None = None,
    ) -> bool:
        """Insert feedback once; return False if request_id already exists."""
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO feedback (request_id, correct_topic, comment, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (request_id, correct_topic, comment, datetime.now(UTC).isoformat()),
                )
                return True
        except sqlite3.IntegrityError:
            return False
