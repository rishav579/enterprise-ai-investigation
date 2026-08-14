"""Evaluation: End-to-end investigation orchestration scenario.

Verifies that the orchestrator executing the "September 2025 churn spike" investigation:

1. Successfully completes all planned steps.
2. Produces evidence covering all required investigation dimensions.
3. SQL results contain the expected anomalous signals in the data.
4. Postmortem document is retrieved.

No LLM is invoked. All assertions are against structured tool outputs.
"""

import pytest
from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.investigation.models import (
    InvestigationRequest,
    InvestigationStatus,
    StepStatus,
)
from src.investigation.orchestrator import InvestigationOrchestrator
from src.investigation.planner import InvestigationPlanner
from src.tools.registry import create_default_tool_registry


@pytest.fixture(scope="module")
def investigation_result(tmp_path_factory):
    """Run the full churn investigation once and share the result across tests."""
    temp = tmp_path_factory.mktemp("eval_orch_data")
    db_url = f"sqlite:///{temp}/eval_orch.db"
    seed_enterprise_database(db_url=db_url, seed=42)

    registry = create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )
    orchestrator = InvestigationOrchestrator(registry=registry)
    request = InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-EVAL-PHASE3",
    )
    return orchestrator.run(request)


def test_eval_investigation_completes_without_failures(investigation_result):
    """Full investigation must complete with no failed or blocked steps."""
    r = investigation_result
    assert r.status == InvestigationStatus.COMPLETED, (
        f"Status was {r.status}. "
        f"Failed: {[s.step_id for s in r.step_results if s.status != StepStatus.COMPLETED]}"
    )
    assert r.failed_steps == 0
    assert r.skipped_steps == 0


def test_eval_all_investigation_dimensions_covered(investigation_result):
    """Every required evidence type must appear in the completed step results."""
    r = investigation_result
    plan = r.plan

    required_evidence_types = {
        "time_series_cancellations",
        "billing_failure_time_series",
        "support_sla_time_series",
        "incident_records",
        "release_records",
        "document_full_text",
    }
    found_types = {
        step.expected_evidence_type
        for step in plan.steps
    }
    missing = required_evidence_types - found_types
    assert not missing, f"Missing evidence types from plan: {missing}"


def test_eval_cancellation_spike_visible_in_step1_result(investigation_result):
    """STEP-01 SQL result must show September 2025 as a high-churn month."""
    r = investigation_result
    step1 = next(s for s in r.step_results if s.step_id == "STEP-01")

    assert step1.status == StepStatus.COMPLETED
    rows = step1.tool_output.get("rows", [])
    assert len(rows) > 0

    monthly_map = {row["churn_month"]: row["total_cancellations"] for row in rows}
    assert "2025-09" in monthly_map

    sept_churn = monthly_map["2025-09"]
    # Should far exceed any single pre-spike month
    baseline_months = [v for k, v in monthly_map.items() if k < "2025-09"]
    assert baseline_months, "Expect at least some baseline months before September"
    max_baseline = max(baseline_months)
    assert sept_churn > max_baseline * 2, (
        f"September churn ({sept_churn}) should be substantially higher than "
        f"best baseline month ({max_baseline})."
    )


def test_eval_billing_failure_surge_visible_in_step3_result(investigation_result):
    """STEP-03 SQL result must show billing failure rate spike in September 2025."""
    r = investigation_result
    step3 = next(s for s in r.step_results if s.step_id == "STEP-03")

    assert step3.status == StepStatus.COMPLETED
    rows = step3.tool_output.get("rows", [])

    sept_row = next((row for row in rows if row.get("month") == "2025-09"), None)
    aug_row = next((row for row in rows if row.get("month") == "2025-08"), None)

    assert sept_row is not None, "September 2025 must appear in billing failure data"
    assert aug_row is not None, "August 2025 must appear for baseline comparison"
    assert sept_row["failure_rate_pct"] > aug_row["failure_rate_pct"] * 3


def test_eval_incident_retrieved_in_step6(investigation_result):
    """STEP-06 must retrieve the P1 billing-gateway incident."""
    r = investigation_result
    step6 = next(s for s in r.step_results if s.step_id == "STEP-06")

    assert step6.status == StepStatus.COMPLETED
    rows = step6.tool_output.get("rows", [])

    billing_incidents = [row for row in rows if row.get("service") == "billing-gateway"]
    assert len(billing_incidents) >= 1

    p1_incidents = [row for row in billing_incidents if row.get("severity") == "P1"]
    assert len(p1_incidents) == 1
    assert p1_incidents[0]["incident_id"] == "INC-2025-002"


def test_eval_postmortem_retrieved_in_step9(investigation_result):
    """STEP-09 must retrieve the full postmortem document with webhook root cause."""
    r = investigation_result
    step9 = next(s for s in r.step_results if s.step_id == "STEP-09")

    assert step9.status == StepStatus.COMPLETED
    content = step9.tool_output.get("content", "")
    assert "billing-gateway" in content
    assert "v2.4.0" in content
    assert "webhook" in content.lower()


def test_eval_investigation_result_suitable_for_evidence_collection(investigation_result):
    """Step results must carry all fields needed for future evidence tagging."""
    r = investigation_result

    for step_result in r.step_results:
        assert step_result.step_id
        assert step_result.status
        assert step_result.tool_name
        assert step_result.tool_input is not None
        if step_result.status == StepStatus.COMPLETED:
            assert step_result.tool_output is not None
            assert step_result.evidence_summary
