from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from app.connectors.base import BaseConnector


class SQLiteConnector(BaseConnector):
    def __init__(self, database: str) -> None:
        self.database = database
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.database)
        self._conn.row_factory = sqlite3.Row

    def test_connection(self) -> bool:
        try:
            self.connect()
            self._conn.execute("SELECT 1")
            return True
        except Exception:
            return False
        finally:
            self.close()

    def get_tables(self) -> List[str]:
        self._ensure_connected()
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]

    def _validate_table(self, table: str) -> None:
        """Raise ValueError if table is not in the list of known tables."""
        known = self.get_tables()
        if table not in known:
            raise ValueError(f"Unknown table: {table!r}")

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        self._validate_table(table)
        self._ensure_connected()
        cursor = self._conn.execute(f"PRAGMA table_info({table})")
        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row["name"],
                    "type": row["type"] or "TEXT",
                    "nullable": not row["notnull"],
                }
            )
        return columns

    def fetch_data(self, table: str, limit: int) -> List[Dict[str, Any]]:
        self._validate_table(table)
        self._ensure_connected()
        cursor = self._conn.execute("SELECT * FROM " + table + " LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_connected(self) -> None:
        if self._conn is None:
            self.connect()
