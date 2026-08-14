"""Service layer for safe, read-only enterprise data querying and introspection."""

from typing import Any, Dict, List, Optional
from sqlalchemy import inspect
from src.data.database import get_engine, execute_read_query


class InvestigationQueryService:
    """Read-only service for analytical query execution and schema discovery."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url

    def get_available_tables(self) -> List[str]:
        """Return list of existing database tables."""
        engine = get_engine(self.db_url)
        inspector = inspect(engine)
        return inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Return column definitions and types for a specific table."""
        engine = get_engine(self.db_url)
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "primary_key": bool(col.get("primary_key", False)),
            }
            for col in columns
        ]

    def query(
        self,
        sql_query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 500,
    ) -> List[Dict[str, Any]]:
        """Execute a read-only SQL query against the enterprise database."""
        return execute_read_query(
            sql_query=sql_query,
            params=params,
            max_rows=max_rows,
            db_url=self.db_url,
        )
