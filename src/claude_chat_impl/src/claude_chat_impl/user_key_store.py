"""Persistent storage for user-specific Claude API keys.

This module provides a lightweight repository backed by SQLite.
It is intentionally framework-agnostic so it can be reused by both
the FastAPI service layer and any other potential clients.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class ClaudeAPIKeyRepository:
    """Stores and retrieves Claude API keys for individual users."""

    def __init__(self, db_path: str) -> None:
        """Initialize the repository with a SQLite database path.

        Args:
            db_path: File path to the SQLite database used to persist
                user → Claude API key mappings. The file is created on
                first use if it does not already exist.

        """
        self._db_path = Path(db_path)
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Create the SQLite database and table if they do not exist."""
        if self._db_path.parent and not self._db_path.parent.exists():
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_claude_keys (
                    user_id TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def set_api_key(self, user_id: str, api_key: str) -> None:
        """Insert or update the Claude API key for a user.

        Args:
            user_id: The authenticated user's unique identifier.
            api_key: The Claude API key to store.

        """
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO user_claude_keys (user_id, api_key, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id)
                DO UPDATE SET api_key=excluded.api_key,
                              updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, api_key),
            )
            connection.commit()

    def get_api_key(self, user_id: str) -> str | None:
        """Retrieve the stored Claude API key for the given user.

        Args:
            user_id: The authenticated user's unique identifier.

        Returns:
            The stored API key if present, otherwise None.

        """
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                """
                SELECT api_key
                FROM user_claude_keys
                WHERE user_id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None
