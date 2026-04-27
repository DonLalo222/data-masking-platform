from __future__ import annotations

from typing import Any, Dict, List

from app.connectors.base import BaseConnector


class SQLServerConnector(BaseConnector):
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
        import pyodbc

        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password}"
        )
        self._conn = pyodbc.connect(connection_string)

    def test_connection(self) -> bool:
        try:
            self.connect()
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
        finally:
            self.close()

    def get_tables(self) -> List[str]:
        self._ensure_connected()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """
        )
        return [row[0] for row in cursor.fetchall()]

    def _validate_table(self, table: str) -> None:
        """Raise ValueError if table is not in the list of known tables."""
        known = self.get_tables()
        if table not in known:
            raise ValueError(f"Unknown table: {table!r}")

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        self._ensure_connected()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            (table,),
        )
        return [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
            }
            for row in cursor.fetchall()
        ]

    def fetch_data(self, table: str, limit: int) -> List[Dict[str, Any]]:
        self._validate_table(table)
        self._ensure_connected()
        cursor = self._conn.cursor()
        cursor.execute(f"SELECT TOP {int(limit)} * FROM [{table}]")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_connected(self) -> None:
        if self._conn is None:
            self.connect()
