from __future__ import annotations

from typing import Any, Dict, List

from app.connectors.base import BaseConnector


class MySQLConnector(BaseConnector):
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
        import pymysql
        import pymysql.cursors

        self._conn = pymysql.connect(
            host=self.host,
            port=self.port,
            db=self.database,
            user=self.username,
            password=self.password,
            cursorclass=pymysql.cursors.DictCursor,
        )

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
        with self._conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            rows = cur.fetchall()
            if rows:
                key = list(rows[0].keys())[0]
                return [row[key] for row in rows]
            return []

    def _validate_table(self, table: str) -> None:
        """Raise ValueError if table is not in the list of known tables."""
        known = self.get_tables()
        if table not in known:
            raise ValueError(f"Unknown table: {table!r}")

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (table,),
            )
            return [
                {
                    "name": row["COLUMN_NAME"],
                    "type": row["DATA_TYPE"],
                    "nullable": row["IS_NULLABLE"] == "YES",
                }
                for row in cur.fetchall()
            ]

    def fetch_data(self, table: str, limit: int) -> List[Dict[str, Any]]:
        self._validate_table(table)
        self._ensure_connected()
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
            return cur.fetchall()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_connected(self) -> None:
        if self._conn is None:
            self.connect()
