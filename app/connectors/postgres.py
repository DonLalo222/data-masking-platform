from __future__ import annotations

from typing import Any, Dict, List

from app.connectors.base import BaseConnector


class PostgreSQLConnector(BaseConnector):
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self._conn = None

    def connect(self) -> None:
        import psycopg2
        import psycopg2.extras

        self._conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.username,
            password=self.password,
        )
        self._cursor_factory = psycopg2.extras.RealDictCursor

    def test_connection(self) -> bool:
        try:
            self.connect()
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            return False
        finally:
            self.close()

    def get_tables(self) -> List[str]:
        self._ensure_connected()
        with self._conn.cursor(cursor_factory=self._cursor_factory) as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            return [row["table_name"] for row in cur.fetchall()]

    def _validate_table(self, table: str) -> None:
        """Raise ValueError if table is not in the list of known tables."""
        known = self.get_tables()
        if table not in known:
            raise ValueError(f"Unknown table: {table!r}")

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self._conn.cursor(cursor_factory=self._cursor_factory) as cur:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                (table,),
            )
            return [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                }
                for row in cur.fetchall()
            ]

    def fetch_data(self, table: str, limit: int) -> List[Dict[str, Any]]:
        self._validate_table(table)
        self._ensure_connected()
        with self._conn.cursor(cursor_factory=self._cursor_factory) as cur:
            cur.execute(f"SELECT * FROM {table} LIMIT %s", (limit,))
            return [dict(row) for row in cur.fetchall()]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_connected(self) -> None:
        if self._conn is None:
            self.connect()
