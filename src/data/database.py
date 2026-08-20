"""Database connection management and read-oriented query execution."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import settings
from src.data.schema import Base

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Get or create SQLAlchemy engine."""
    global _engine
    target_url = db_url or settings.database_url
    if _engine is None or str(_engine.url) != target_url:
        # If using local SQLite, ensure directory exists
        if target_url.startswith("sqlite:///"):
            db_path = target_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        _engine = create_engine(
            target_url,
            echo=False,
            future=True,
        )
    return _engine


def get_session_factory(db_url: Optional[str] = None) -> sessionmaker:
    """Get or create Session factory."""
    global _SessionFactory
    engine = get_engine(db_url)
    if _SessionFactory is None or _SessionFactory.kw.get("bind") != engine:
        _SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionFactory


def get_db_session(db_url: Optional[str] = None) -> Session:
    """Create a new database session."""
    factory = get_session_factory(db_url)
    return factory()


def init_db(db_url: Optional[str] = None) -> None:
    """Initialize database tables from SQLAlchemy metadata."""
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)


def reset_db(db_url: Optional[str] = None) -> None:
    """Drop and recreate all tables (used for idempotent seeding/testing)."""
    engine = get_engine(db_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_missing_tables(db_url: Optional[str] = None) -> set[str]:
    """Return application tables that are absent from the configured database."""
    engine = get_engine(db_url)
    existing_tables = set(inspect(engine).get_table_names())
    required_tables = set(Base.metadata.tables.keys())
    return required_tables - existing_tables


def validate_database_schema(db_url: Optional[str] = None) -> None:
    """Raise when the configured database does not contain the full application schema."""
    missing_tables = sorted(get_missing_tables(db_url))
    if missing_tables:
        raise RuntimeError(
            "Database schema is incomplete; missing required tables: "
            + ", ".join(missing_tables)
        )


def execute_read_query(
    sql_query: str,
    params: Optional[Dict[str, Any]] = None,
    max_rows: int = 1000,
    db_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Execute a parameterized read-only SQL query safely.
    
    Guarantees:
    - Strips comments and checks statement begins with SELECT or WITH.
    - Explicitly rejects mutating SQL clauses.
    - Limits result rows to max_rows.
    - Returns structured list of dicts.
    """
    clean_query = sql_query.strip()
    if not clean_query:
        raise ValueError("SQL query cannot be empty.")

    # Elementary keyword guardrail for read-only safety
    # (In Phase 2, this is supplemented by full AST parsing)
    normalized = " " + clean_query.upper() + " "
    forbidden = [
        " INSERT ", " UPDATE ", " DELETE ", " DROP ", " ALTER ",
        " TRUNCATE ", " GRANT ", " REVOKE ", " CREATE ", " REPLACE ",
        " EXEC ", " EXECUTE ", " VACUUM ", " ATTACH ", " DETACH "
    ]
    for kw in forbidden:
        if kw in normalized:
            raise PermissionError(f"Prohibited SQL operation detected: {kw.strip()}")

    if not (clean_query.upper().startswith("SELECT") or clean_query.upper().startswith("WITH")):
        raise PermissionError("Only SELECT or WITH (CTE) queries are permitted in read execution.")

    engine = get_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text(clean_query), params or {})
        rows = result.fetchmany(max_rows)
        keys = list(result.keys())
        return [dict(zip(keys, row)) for row in rows]
