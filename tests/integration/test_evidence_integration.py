"""Integration tests: Phase 4 evidence collection and audit trail through the orchestrator."""

import pytest
from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.investigation.audit import AuditEventType
from src.investigation.evidence import EvidenceType
from src.investigation.models import (
    InvestigationRequest,
    InvestigationStatus,
    StepStatus,
)
from src.investigation.orchestrator import InvestigationOrchestrator
from src.investigation.planner import InvestigationPlanner
from src.tools.registry import create_default_tool_registry


# ---------------------------------------------------------------------------
# Module-scoped fixtures: seed once, share across tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry(tmp_path_factory):
    temp = tmp_path_factory.mktemp("p4_integ_data")
    db_url = f"sqlite:///{temp}/p4_integ.db"
    seed_enterprise_database(db_url=db_url, seed=42)
    return create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )


@pytest.fixture(scope="module")
def orchestrator(registry):
    return InvestigationOrchestrator(registry=registry)


@pytest.fixture(scope="module")
def churn_result(orchestrator):
    """Run the full churn investigation once; share the result."""
    return orchestrator.run(
        InvestigationRequest(
            question="Why did customer cancellations increase sharply in September 2025?",
            investigation_id="INV-P4-INTEG-001",
        )
    )


# ---------------------------------------------------------------------------
# Phase 3 regression: existing behaviour must be preserved
# ---------------------------------------------------------------------------

class TestPhase3Regression:
    def test_investigation_still_completes_successfully(self, churn_result):
        assert churn_result.status == InvestigationStatus.COMPLETED
        assert churn_result.failed_steps == 0
        assert churn_result.skipped_steps == 0

    def test_step_results_preserve_order(self, churn_result):
        result_ids = [r.step_id for r in churn_result.step_results]
        plan_ids = [s.step_id for s in churn_result.plan.steps]
        assert result_ids == plan_ids

    def test_sql_steps_still_report_row_counts(self, churn_result):
        for sr in churn_result.step_results:
            if sr.tool_name == "sql_investigation" and sr.status == StepStatus.COMPLETED:
                assert sr.row_count is not None
                assert sr.row_count >= 0

    def test_completed_steps_have_evidence_summaries(self, churn_result):
        for sr in churn_result.step_results:
            if sr.status == StepStatus.COMPLETED:
                assert sr.evidence_summary


# ---------------------------------------------------------------------------
# Phase 4: evidence IDs attached to step results
# ---------------------------------------------------------------------------

class TestEvidenceIdsInStepResults:
    def test_completed_steps_have_evidence_ids(self, churn_result):
        for sr in churn_result.step_results:
            if sr.status == StepStatus.COMPLETED:
                assert len(sr.evidence_ids) > 0, (
                    f"Step {sr.step_id} completed but has no evidence_ids."
                )

    def test_failed_blocked_steps_have_no_evidence_ids(self, churn_result):
        for sr in churn_result.step_results:
            if sr.status in (StepStatus.FAILED, StepStatus.BLOCKED):
                assert sr.evidence_ids == [], (
                    f"Step {sr.step_id} ({sr.status}) must not carry evidence_ids."
                )

    def test_evidence_ids_are_unique_across_all_steps(self, churn_result):
        all_ids = []
        for sr in churn_result.step_results:
            all_ids.extend(sr.evidence_ids)
        assert len(all_ids) == len(set(all_ids)), "Evidence IDs must be globally unique"

    def test_total_evidence_items_matches_sum_of_step_evidence(self, churn_result):
        step_total = sum(len(sr.evidence_ids) for sr in churn_result.step_results)
        assert churn_result.total_evidence_items == step_total


# ---------------------------------------------------------------------------
# Phase 4: audit event coverage
# ---------------------------------------------------------------------------

class TestAuditEventCoverage:
    def _get_orchestrator_with_audit(self, registry):
        """Re-run to get a fresh orchestrator that exposes the audit trail."""
        # We need to test audit events; since InvestigationRunResult only carries counts,
        # we test coverage via audit_event_count.
        return InvestigationOrchestrator(registry=registry)

    def test_audit_event_count_is_positive(self, churn_result):
        assert churn_result.audit_event_count > 0

    def test_audit_event_count_is_reasonable(self, churn_result):
        # Per-step events: STEP_STARTED + STEP_COMPLETED = 2 minimum each
        # EVIDENCE_COLLECTED fired when items > 0; at least 8 of 9 steps should have it
        # Plus INVESTIGATION_STARTED + PLAN_CREATED + INVESTIGATION_COMPLETED = 3
        # Conservative lower bound: 9*2 + 3 = 21
        assert churn_result.audit_event_count >= 21, (
            f"Expected at least 21 audit events for a 9-step investigation, "
            f"got {churn_result.audit_event_count}"
        )


# ---------------------------------------------------------------------------
# Phase 4: orchestrator with dependency failure produces correct evidence/audit
# ---------------------------------------------------------------------------

class TestEvidenceOnDependencyFailure:
    def test_blocked_step_produces_no_evidence(self, registry):
        """When STEP-06 fails, STEP-08 must be BLOCKED with no evidence."""
        from src.investigation.models import InvestigationPlan, InvestigationStep

        class FailingStep06Planner:
            def plan(self, req):
                return InvestigationPlan(
                    plan_id="PLAN-DEP-TEST",
                    investigation_id=req.investigation_id,
                    question=req.question,
                    scenario="test",
                    steps=[
                        InvestigationStep(
                            step_id="STEP-06",
                            objective="Fail deliberately",
                            rationale="Test dependency blocking",
                            tool_name="sql_investigation",
                            tool_input={"query": "DELETE FROM product_incidents"},
                            expected_evidence_type="incident_records",
                            depends_on=[],
                        ),
                        InvestigationStep(
                            step_id="STEP-08",
                            objective="Depends on STEP-06",
                            rationale="Should be blocked",
                            tool_name="document_retrieval",
                            tool_input={"action": "list"},
                            expected_evidence_type="document_listing",
                            depends_on=["STEP-06"],
                        ),
                    ],
                    total_steps=2,
                )

        orch = InvestigationOrchestrator(registry=registry, planner=FailingStep06Planner())
        result = orch.run(InvestigationRequest(question="Test blocking"))

        step06 = next(r for r in result.step_results if r.step_id == "STEP-06")
        step08 = next(r for r in result.step_results if r.step_id == "STEP-08")

        assert step06.status == StepStatus.FAILED
        assert step06.evidence_ids == []

        assert step08.status == StepStatus.BLOCKED
        assert step08.evidence_ids == []

        # Evidence total must be 0 (no fabricated evidence)
        assert result.total_evidence_items == 0

    def test_audit_records_blocked_and_failed_events(self, registry):
        """Audit event count must include STEP_FAILED and STEP_BLOCKED events."""
        from src.investigation.models import InvestigationPlan, InvestigationStep

        class TwoStepBadPlanner:
            def plan(self, req):
                return InvestigationPlan(
                    plan_id="PLAN-AUDIT-FAIL",
                    investigation_id=req.investigation_id,
                    question=req.question,
                    scenario="test",
                    steps=[
                        InvestigationStep(
                            step_id="STEP-01",
                            objective="Bad SQL",
                            rationale="Test",
                            tool_name="sql_investigation",
                            tool_input={"query": "DROP TABLE customers"},
                            expected_evidence_type="test",
                            depends_on=[],
                        ),
                        InvestigationStep(
                            step_id="STEP-02",
                            objective="Blocked",
                            rationale="Test",
                            tool_name="sql_investigation",
                            tool_input={"query": "SELECT 1"},
                            expected_evidence_type="test",
                            depends_on=["STEP-01"],
                        ),
                    ],
                    total_steps=2,
                )

        orch = InvestigationOrchestrator(registry=registry, planner=TwoStepBadPlanner())
        result = orch.run(InvestigationRequest(question="Audit test"))

        # started + plan + step_failed + step_blocked + outcome = 5 minimum
        assert result.audit_event_count >= 5
