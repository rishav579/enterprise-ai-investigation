"""Integration tests for deterministic database seeding and idempotency."""

import pytest
from src.data.seed_database import seed_enterprise_database
from src.data.database import execute_read_query


@pytest.fixture
def clean_test_db(tmp_path):
    """Fixture providing a temporary SQLite file database URL."""
    db_file = tmp_path / "test_enterprise.db"
    return f"sqlite:///{db_file}"


def test_seed_database_execution_and_idempotency(clean_test_db):
    """Verify that seeding populates all tables and repeated runs produce identical deterministic counts."""
    # First seed run
    counts_1 = seed_enterprise_database(db_url=clean_test_db, seed=42)

    assert counts_1["customers"] == 500
    assert counts_1["subscriptions"] == 500
    assert counts_1["billing_events"] > 0
    assert counts_1["support_tickets"] > 0
    assert counts_1["product_incidents"] == 3
    assert counts_1["release_events"] == 5

    # Second seed run (must be idempotent and overwrite cleanly without duplication)
    counts_2 = seed_enterprise_database(db_url=clean_test_db, seed=42)
    assert counts_1 == counts_2

    # Verify customer count in database directly matches
    customer_rows = execute_read_query("SELECT COUNT(*) AS cnt FROM customers", db_url=clean_test_db)
    assert customer_rows[0]["cnt"] == 500


def test_foreign_key_referential_integrity(clean_test_db):
    """Verify that all subscriptions, billing events, and support tickets map to valid customers."""
    seed_enterprise_database(db_url=clean_test_db, seed=42)

    # Check for orphaned subscriptions
    orphaned_subs = execute_read_query(
        """
        SELECT s.subscription_id
        FROM subscriptions s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        """,
        db_url=clean_test_db,
    )
    assert len(orphaned_subs) == 0

    # Check for orphaned billing events
    orphaned_bills = execute_read_query(
        """
        SELECT b.billing_event_id
        FROM billing_events b
        LEFT JOIN customers c ON b.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        """,
        db_url=clean_test_db,
    )
    assert len(orphaned_bills) == 0

    # Check for orphaned support tickets
    orphaned_tickets = execute_read_query(
        """
        SELECT t.ticket_id
        FROM support_tickets t
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        """,
        db_url=clean_test_db,
    )
    assert len(orphaned_tickets) == 0
