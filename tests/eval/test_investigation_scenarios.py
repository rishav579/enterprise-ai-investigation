"""Deterministic tool-level investigation scenario tests.

Verifies that the controlled SQL and Document tools can successfully uncover
all facts required to solve the enterprise churn anomaly:
1. Cancellation rate by month (detecting the Sept-Oct surge).
2. Billing failure rate by month (detecting the September payment failure surge).
3. Support ticket volume and resolution time by month (detecting the September SLA degradation).
4. Cancellations by customer segment and region (identifying Enterprise/Pro and EU/US concentration).
5. Release events during the affected period (identifying billing-gateway v2.4.0 on Sept 2).
6. Incident lookup (identifying P1 incident on Sept 5).
7. Document retrieval (retrieving incident postmortem explaining the webhook root cause).
"""

from pathlib import Path
import pytest
from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.tools import (
    SQLInvestigationTool,
    DocumentRetrievalTool,
    create_default_tool_registry,
)


@pytest.fixture(scope="module")
def investigation_env(tmp_path_factory):
    """Set up database and document environment for investigation scenario tests."""
    temp_dir = tmp_path_factory.mktemp("inv_scenario")
    db_file = temp_dir / "investigation_scenario.db"
    db_url = f"sqlite:///{db_file}"
    seed_enterprise_database(db_url=db_url, seed=42)

    doc_dir = PROJECT_ROOT / "data" / "raw"
    registry = create_default_tool_registry(db_url=db_url, doc_dir=doc_dir)

    return {"db_url": db_url, "doc_dir": doc_dir, "registry": registry}


def test_scenario_1_cancellation_rate_by_month(investigation_env):
    """Scenario Step 1: Query cancellation counts grouped by month to establish timeline."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT 
        strftime('%Y-%m', cancellation_date) AS churn_month,
        COUNT(*) AS total_cancellations
    FROM subscriptions
    WHERE cancellation_date IS NOT NULL
    GROUP BY churn_month
    ORDER BY churn_month ASC
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    assert len(result.rows) > 0

    # Locate September 2025 in the result
    monthly_map = {r["churn_month"]: r["total_cancellations"] for r in result.rows}
    assert "2025-09" in monthly_map
    sept_churn = monthly_map["2025-09"]

    # Compare against earlier baseline months
    aug_churn = monthly_map.get("2025-08", 0)
    assert sept_churn > (aug_churn * 3), "September churn should clearly spike over August baseline."


def test_scenario_2_billing_failure_rate_by_month(investigation_env):
    """Scenario Step 2: Query billing transactions to detect payment failure rates."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT 
        strftime('%Y-%m', event_date) AS month,
        COUNT(*) AS total_charges,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_charges,
        ROUND(100.0 * SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_percentage
    FROM billing_events
    GROUP BY month
    ORDER BY month ASC
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    month_data = {r["month"]: r["failure_percentage"] for r in result.rows}

    assert month_data["2025-08"] < 5.0
    assert month_data["2025-09"] > 15.0


def test_scenario_3_support_volume_and_resolution_time(investigation_env):
    """Scenario Step 3: Query support ticket volume and resolution hours by month."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT 
        strftime('%Y-%m', created_at) AS ticket_month,
        COUNT(*) AS total_tickets,
        ROUND(AVG((julianday(resolved_at) - julianday(created_at)) * 24.0), 1) AS avg_resolution_hours
    FROM support_tickets
    WHERE resolved_at IS NOT NULL
    GROUP BY ticket_month
    ORDER BY ticket_month ASC
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    sept_ticket_row = next(r for r in result.rows if r["ticket_month"] == "2025-09")
    assert sept_ticket_row["total_tickets"] > 50
    assert sept_ticket_row["avg_resolution_hours"] > 30.0


def test_scenario_4_cancellations_by_segment_and_plan(investigation_env):
    """Scenario Step 4: Correlate cancellations with customer segment and plan."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT 
        c.plan,
        c.region,
        COUNT(s.subscription_id) AS cancelled_count
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    WHERE s.cancellation_date >= '2025-09-01'
    GROUP BY c.plan, c.region
    ORDER BY cancelled_count DESC
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    # Verify top impacted combinations are Enterprise/Pro in EU-Central / US-East
    top_impact = result.rows[0]
    assert top_impact["plan"] in ("pro", "enterprise")
    assert top_impact["region"] in ("EU-Central", "US-East")


def test_scenario_5_release_events_lookup(investigation_env):
    """Scenario Step 5: Check software releases around the anomaly start date (Sept 2025)."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT release_id, release_date, service, version, change_type
    FROM release_events
    WHERE release_date >= '2025-08-15' AND release_date <= '2025-09-15'
    ORDER BY release_date ASC
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    services = [r["service"] for r in result.rows]
    assert "billing-gateway" in services

    billing_release = next(r for r in result.rows if r["service"] == "billing-gateway")
    assert billing_release["version"] == "v2.4.0"
    assert billing_release["release_date"] == "2025-09-02"


def test_scenario_6_product_incident_lookup(investigation_env):
    """Scenario Step 6: Query platform incidents occurring in September 2025."""
    sql_tool = investigation_env["registry"].get("sql_investigation")

    query = """
    SELECT incident_id, incident_date, severity, service, description
    FROM product_incidents
    WHERE incident_date >= '2025-09-01' AND severity = 'P1'
    """
    result = sql_tool.execute({"query": query})

    assert result.success is True
    assert len(result.rows) == 1
    assert result.rows[0]["incident_id"] == "INC-2025-002"
    assert result.rows[0]["service"] == "billing-gateway"


def test_scenario_7_document_postmortem_retrieval(investigation_env):
    """Scenario Step 7: Search and retrieve internal postmortem document explaining root cause."""
    doc_tool = investigation_env["registry"].get("document_retrieval")

    # 1. Search for webhook mentions in docs
    search_res = doc_tool.execute({
        "action": "search",
        "query": "webhook",
    })
    assert search_res.success is True
    assert search_res.total_matches > 0

    target_doc_id = search_res.matches[0].document_id
    assert "postmortem" in target_doc_id

    # 2. Get full content of the postmortem
    get_res = doc_tool.execute({
        "action": "get",
        "document_id": target_doc_id,
    })
    assert get_res.success is True
    assert "billing-gateway" in get_res.content
    assert "v2.4.0" in get_res.content
    assert "3DS" in get_res.content
