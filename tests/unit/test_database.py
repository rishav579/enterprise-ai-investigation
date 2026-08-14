"""Unit tests for database initialization, read operations, and security constraints."""

import pytest
from sqlalchemy import text
from src.data.database import (
    get_engine,
    init_db,
    execute_read_query,
    reset_db,
)


@pytest.fixture
def temp_db():
    """Fixture providing a clean SQLite test database URL."""
    test_db_url = "sqlite:///:memory:"
    init_db(test_db_url)
    return test_db_url


def test_init_and_reset_db(temp_db):
    """Test database tables can be created and reset cleanly."""
    reset_db(temp_db)
    engine = get_engine(temp_db)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]

    assert "customers" in tables
    assert "subscriptions" in tables
    assert "billing_events" in tables
    assert "support_tickets" in tables
    assert "product_incidents" in tables
    assert "release_events" in tables


def test_execute_read_query_success(temp_db):
    """Test safe read-only SELECT execution."""
    engine = get_engine(temp_db)
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO product_incidents (incident_id, incident_date, severity, service, description) VALUES ('INC-TEST', '2025-09-01', 'P1', 'auth', 'Test incident');"))
        conn.commit()

    results = execute_read_query(
        "SELECT incident_id, severity, service FROM product_incidents WHERE severity = :sev",
        params={"sev": "P1"},
        db_url=temp_db,
    )
    assert len(results) == 1
    assert results[0]["incident_id"] == "INC-TEST"
    assert results[0]["severity"] == "P1"


def test_execute_read_query_row_limit(temp_db):
    """Test row limit truncation in execute_read_query."""
    engine = get_engine(temp_db)
    with engine.connect() as conn:
        for i in range(10):
            conn.execute(
                text(f"INSERT INTO product_incidents (incident_id, incident_date, severity, service, description) VALUES ('INC-{i}', '2025-09-01', 'P2', 'api', 'desc');")
            )
        conn.commit()

    results = execute_read_query(
        "SELECT * FROM product_incidents",
        max_rows=3,
        db_url=temp_db,
    )
    assert len(results) == 3


@pytest.mark.parametrize("malicious_query", [
    "DELETE FROM customers;",
    "DROP TABLE subscriptions;",
    "UPDATE subscriptions SET status = 'active';",
    "INSERT INTO customers VALUES ('hacked', 'a', 'b', '2025-01-01', 'c');",
    "TRUNCATE TABLE billing_events;",
    "ALTER TABLE customers ADD COLUMN secret TEXT;",
])
def test_execute_read_query_rejects_destructive_operations(temp_db, malicious_query):
    """Verify that destructive SQL operations are strictly blocked by guardrails."""
    with pytest.raises(PermissionError):
        execute_read_query(malicious_query, db_url=temp_db)
