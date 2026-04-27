from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseConnector(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Establish the connection to the database."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Return True if the connection can be established successfully."""

    @abstractmethod
    def get_tables(self) -> List[str]:
        """Return a list of table names in the database."""

    @abstractmethod
    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """Return column metadata for *table*.

        Each entry should have the keys:
        - name (str)
        - type (str)
        - nullable (bool)
        """

    @abstractmethod
    def fetch_data(self, table: str, limit: int) -> List[Dict[str, Any]]:
        """Return up to *limit* rows from *table* as a list of dicts."""

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
