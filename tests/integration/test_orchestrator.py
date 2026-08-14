"""Integration tests for the InvestigationOrchestrator."""

from pathlib import Path
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
from src.tools.registry import ToolRegistry, create_default_tool_registry
from src.tools.sql_tool import SQLInvestigationTool
from src.tools.document_tool import DocumentRetrievalTool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_registry(tmp_path_factory):
    """Shared seeded registry for orchestrator integration tests."""
    temp = tmp_path_factory.mktemp("orch_data")
    db_url = f"sqlite:///{temp}/orch_test.db"
    seed_enterprise_database(db_url=db_url, seed=42)
    doc_dir = PROJECT_ROOT / "data" / "raw"
    return create_default_tool_registry(db_url=db_url, doc_dir=doc_dir)


@pytest.fixture(scope="module")
def orchestrator(seeded_registry):
    return InvestigationOrchestrator(registry=seeded_registry)


@pytest.fixture
def churn_request():
    return InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-ORCH-001",
    )


# ---------------------------------------------------------------------------
# Orchestrator tests
# ---------------------------------------------------------------------------

def test_orchestrator_returns_structured_run_result(orchestrator, churn_request):
    """Orchestrator must return a fully populated InvestigationRunResult."""
    result = orchestrator.run(churn_request)

    assert result.investigation_id == churn_request.investigation_id
    assert result.question == churn_request.question
    assert result.plan is not None
    assert len(result.step_results) == result.total_steps
    assert result.completed_steps + result.failed_steps + result.skipped_steps == result.total_steps


def test_orchestrator_completes_successfully_with_seeded_data(orchestrator, churn_request):
    """With a fully seeded database, all steps should complete without failures."""
    result = orchestrator.run(churn_request)

    assert result.status == InvestigationStatus.COMPLETED, (
        f"Expected COMPLETED but got {result.status}. "
        f"Failures: {[r for r in result.step_results if r.status != StepStatus.COMPLETED]}"
    )
    assert result.completed_steps == result.total_steps
    assert result.failed_steps == 0
    assert result.skipped_steps == 0


def test_orchestrator_step_results_preserve_order(orchestrator, churn_request):
    """Step results must be returned in plan order (STEP-01, STEP-02, ...)."""
    result = orchestrator.run(churn_request)

    result_ids = [r.step_id for r in result.step_results]
    plan_ids = [s.step_id for s in result.plan.steps]
    assert result_ids == plan_ids


def test_orchestrator_completed_steps_have_evidence_summaries(orchestrator, churn_request):
    """Completed steps must include non-empty evidence summaries."""
    result = orchestrator.run(churn_request)

    for step_result in result.step_results:
        if step_result.status == StepStatus.COMPLETED:
            assert step_result.evidence_summary, (
                f"Step {step_result.step_id} completed but has no evidence_summary."
            )
            assert step_result.tool_output is not None


def test_orchestrator_sql_steps_report_row_counts(orchestrator, churn_request):
    """SQL investigation steps must populate the row_count field in their results."""
    result = orchestrator.run(churn_request)

    for step_result in result.step_results:
        if step_result.tool_name == "sql_investigation" and step_result.status == StepStatus.COMPLETED:
            assert step_result.row_count is not None, (
                f"Step {step_result.step_id} (SQL) should have row_count populated."
            )
            assert step_result.row_count >= 0


def test_orchestrator_blocks_dependent_step_on_dependency_failure(seeded_registry):
    """A step whose dependency failed must receive BLOCKED status and not execute."""
    planner = InvestigationPlanner()
    orchestrator = InvestigationOrchestrator(registry=seeded_registry, planner=planner)

    request = InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-DEP-TEST",
        max_steps=9,
    )
    plan = planner.plan(request)

    # Locate STEP-08 which depends on STEP-06
    step_08 = next(s for s in plan.steps if s.step_id == "STEP-08")
    assert "STEP-06" in step_08.depends_on

    # Inject a failing STEP-06 by running with a bad SQL query:
    # Patch the plan to replace STEP-06 with a bad query
    from src.investigation.models import InvestigationStep
    bad_steps = []
    for step in plan.steps:
        if step.step_id == "STEP-06":
            bad_steps.append(
                InvestigationStep(
                    step_id=step.step_id,
                    objective=step.objective,
                    rationale=step.rationale,
                    tool_name="sql_investigation",
                    tool_input={"query": "DELETE FROM product_incidents"},  # will be rejected
                    expected_evidence_type=step.expected_evidence_type,
                    depends_on=step.depends_on,
                )
            )
        else:
            bad_steps.append(step)

    from src.investigation.models import InvestigationPlan
    patched_plan = InvestigationPlan(
        plan_id=plan.plan_id,
        investigation_id=plan.investigation_id,
        question=plan.question,
        scenario=plan.scenario,
        steps=bad_steps,
        total_steps=len(bad_steps),
    )

    # Monkey-patch planner to return our custom plan
    class FixedPlanner:
        def plan(self, req):
            return patched_plan

    orch = InvestigationOrchestrator(registry=seeded_registry, planner=FixedPlanner())
    result = orch.run(request)

    result_by_id = {r.step_id: r for r in result.step_results}
    assert result_by_id["STEP-06"].status == StepStatus.FAILED
    assert result_by_id["STEP-08"].status == StepStatus.BLOCKED
    assert result_by_id["STEP-09"].status == StepStatus.BLOCKED


def test_orchestrator_rejects_unregistered_tool(seeded_registry):
    """Orchestrator must fail gracefully when a step references a tool not in registry."""
    from src.investigation.models import InvestigationPlan, InvestigationStep

    class BadToolPlanner:
        def plan(self, req):
            return InvestigationPlan(
                plan_id="PLAN-BAD",
                investigation_id=req.investigation_id,
                question=req.question,
                scenario="test",
                steps=[
                    InvestigationStep(
                        step_id="STEP-01",
                        objective="Test bad tool",
                        rationale="Testing unregistered tool rejection",
                        tool_name="nonexistent_tool",
                        tool_input={"query": "SELECT 1"},
                        expected_evidence_type="test",
                        depends_on=[],
                    )
                ],
                total_steps=1,
            )

    orch = InvestigationOrchestrator(registry=seeded_registry, planner=BadToolPlanner())
    result = orch.run(InvestigationRequest(question="Test question"))

    assert result.step_results[0].status == StepStatus.FAILED
    assert result.failed_steps == 1
    assert result.status == InvestigationStatus.FAILED
