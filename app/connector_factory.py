from __future__ import annotations

from app.connectors.base import BaseConnector


def get_connector(conn_data: dict) -> BaseConnector:
    """Return the appropriate connector instance for a stored connection dict."""
    db_type = conn_data["db_type"]

    if db_type == "sqlite":
        from app.connectors.sqlite import SQLiteConnector
        return SQLiteConnector(database=conn_data["database"])

    if db_type == "postgres":
        from app.connectors.postgres import PostgreSQLConnector
        return PostgreSQLConnector(
            host=conn_data["host"],
            port=conn_data["port"],
            database=conn_data["database"],
            username=conn_data["username"],
            password=conn_data["password"],
        )

    if db_type == "mysql":
        from app.connectors.mysql import MySQLConnector
        return MySQLConnector(
            host=conn_data["host"],
            port=conn_data["port"],
            database=conn_data["database"],
            username=conn_data["username"],
            password=conn_data["password"],
        )

    if db_type == "sqlserver":
        from app.connectors.sqlserver import SQLServerConnector
        return SQLServerConnector(
            host=conn_data["host"],
            port=conn_data["port"],
            database=conn_data["database"],
            username=conn_data["username"],
            password=conn_data["password"],
        )

    raise ValueError(f"Unsupported db_type: {db_type}")
