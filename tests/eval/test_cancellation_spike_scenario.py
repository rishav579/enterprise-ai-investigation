"""Deterministic evaluation of the planted enterprise investigation scenario.

Verifies that the synthetic dataset contains the intended multi-table business signals:
1. Significant statistical surge in cancellations during the Sept-Oct 2025 period vs baseline.
2. Significant rise in payment failure rate during the incident window.
3. Severe support resolution latency degradation in September 2025.
4. Documented release event and P1 incident on the billing gateway.
"""

import pytest
from src.data.seed_database import seed_enterprise_database
from src.data.database import execute_read_query


@pytest.fixture(scope="module")
def eval_db(tmp_path_factory):
    """Create a seeded database once for evaluation tests."""
    temp_dir = tmp_path_factory.mktemp("eval_data")
    db_url = f"sqlite:///{temp_dir}/eval_enterprise.db"
    seed_enterprise_database(db_url=db_url, seed=42)
    return db_url


def test_planted_cancellation_spike_is_present(eval_db):
    """Verify customer cancellations show a statistically significant surge in Sept-Oct 2025."""
    # Monthly cancellations baseline (Jan 1 to Aug 31, 2025 -> 8 months)
    baseline_query = """
    SELECT COUNT(*) AS total_cancelled
    FROM subscriptions
    WHERE cancellation_date >= '2025-01-01' AND cancellation_date < '2025-09-01'
    """
    baseline_res = execute_read_query(baseline_query, db_url=eval_db)
    baseline_total = baseline_res[0]["total_cancelled"]
    baseline_monthly_avg = baseline_total / 8.0

    # Investigation window cancellations (Sept 1 to Oct 15, 2025 -> 1.5 months)
    spike_query = """
    SELECT COUNT(*) AS total_cancelled
    FROM subscriptions
    WHERE cancellation_date >= '2025-09-01' AND cancellation_date <= '2025-10-15'
    """
    spike_res = execute_read_query(spike_query, db_url=eval_db)
    spike_total = spike_res[0]["total_cancelled"]
    spike_monthly_rate = spike_total / 1.5

    # Assert that the spike monthly cancellation rate is at least 5x the baseline monthly average
    assert baseline_total > 0, "Baseline should have non-zero organic cancellations."
    assert spike_total > baseline_total, "Spike period should have more total cancellations than 8 months of baseline."
    assert (spike_monthly_rate / baseline_monthly_avg) >= 5.0, (
        f"Expected at least 5x surge in monthly cancellation rate. "
        f"Baseline avg: {baseline_monthly_avg:.2f}/mo, Spike rate: {spike_monthly_rate:.2f}/mo"
    )


def test_planted_billing_failure_surge_is_present(eval_db):
    """Verify that billing failure rate spikes sharply in September 2025."""
    # Baseline failed charge rate in August 2025
    aug_query = """
    SELECT 
        COUNT(*) AS total_events,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_events
    FROM billing_events
    WHERE event_date >= '2025-08-01' AND event_date <= '2025-08-31'
    """
    aug_res = execute_read_query(aug_query, db_url=eval_db)
    aug_failure_rate = (aug_res[0]["failed_events"] or 0) / aug_res[0]["total_events"]

    # Spike period failed charge rate in September 2025
    sept_query = """
    SELECT 
        COUNT(*) AS total_events,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_events
    FROM billing_events
    WHERE event_date >= '2025-09-01' AND event_date <= '2025-09-30'
    """
    sept_res = execute_read_query(sept_query, db_url=eval_db)
    sept_failure_rate = (sept_res[0]["failed_events"] or 0) / sept_res[0]["total_events"]

    assert aug_failure_rate < 0.05, f"August failure rate was unexpectedly high: {aug_failure_rate:.2%}"
    assert sept_failure_rate > 0.15, f"September failure rate was unexpectedly low: {sept_failure_rate:.2%}"
    assert sept_failure_rate > (aug_failure_rate * 3.0), "September failure rate must be at least 3x August baseline."


def test_planted_support_latency_degradation_is_present(eval_db):
    """Verify that support ticket resolution hours surged dramatically in September 2025."""
    # Baseline average resolution duration in July/August
    baseline_query = """
    SELECT 
        AVG((julianday(resolved_at) - julianday(created_at)) * 24.0) AS avg_resolution_hours
    FROM support_tickets
    WHERE created_at >= '2025-01-01' AND created_at < '2025-09-01' AND resolved_at IS NOT NULL
    """
    baseline_res = execute_read_query(baseline_query, db_url=eval_db)
    baseline_hours = baseline_res[0]["avg_resolution_hours"]

    # September resolution duration
    sept_query = """
    SELECT 
        AVG((julianday(resolved_at) - julianday(created_at)) * 24.0) AS avg_resolution_hours
    FROM support_tickets
    WHERE created_at >= '2025-09-01' AND created_at <= '2025-09-30' AND resolved_at IS NOT NULL
    """
    sept_res = execute_read_query(sept_query, db_url=eval_db)
    sept_hours = sept_res[0]["avg_resolution_hours"]

    assert baseline_hours < 10.0, f"Baseline support hours unexpectedly high: {baseline_hours:.1f} hrs"
    assert sept_hours > 30.0, f"September support hours unexpectedly low: {sept_hours:.1f} hrs"


def test_planted_root_cause_events_exist(eval_db):
    """Verify the existence of the critical release event and P1 incident on the billing service."""
    releases = execute_read_query(
        "SELECT * FROM release_events WHERE service = 'billing-gateway' AND version = 'v2.4.0'",
        db_url=eval_db,
    )
    assert len(releases) == 1
    assert releases[0]["release_date"] == "2025-09-02"

    incidents = execute_read_query(
        "SELECT * FROM product_incidents WHERE severity = 'P1' AND service = 'billing-gateway'",
        db_url=eval_db,
    )
    assert len(incidents) == 1
    assert incidents[0]["incident_date"] == "2025-09-05"
    assert "webhook" in incidents[0]["description"].lower()
