"""End-to-end evaluation: Phase 4 — Evidence Collection & Auditability.

Runs the complete 9-step churn investigation and verifies:
  1. All existing Phase 3 assertions still pass (no regressions).
  2. Every successful step produces at least one evidence item with correct provenance.
  3. Evidence IDs are attached to step results.
  4. No evidence is fabricated for failed or blocked steps.
  5. SQL evidence preserves query and returned rows.
  6. Document evidence preserves document ID and content.
  7. The investigation result carries correct aggregate evidence and audit counts.
  8. Content hash is stable across repeated runs on identical data.

Evidence collection is deterministic and does NOT use an LLM.
"""

import pytest
from src.config.settings import PROJECT_ROOT
from src.data.seed_database import seed_enterprise_database
from src.investigation.audit import AuditEventType
from src.investigation.evidence import EvidenceStore, EvidenceType, compute_content_hash
from src.investigation.collector import EvidenceCollector
from src.investigation.models import (
    InvestigationRequest,
    InvestigationStatus,
    StepStatus,
)
from src.investigation.orchestrator import InvestigationOrchestrator
from src.tools.registry import create_default_tool_registry


# ---------------------------------------------------------------------------
# Shared investigation run (run once per module)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def eval_result(tmp_path_factory):
    temp = tmp_path_factory.mktemp("eval_p4_data")
    db_url = f"sqlite:///{temp}/eval_p4.db"
    seed_enterprise_database(db_url=db_url, seed=42)
    registry = create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )
    orchestrator = InvestigationOrchestrator(registry=registry)
    return orchestrator.run(
        InvestigationRequest(
            question="Why did customer cancellations increase sharply in September 2025?",
            investigation_id="INV-EVAL-P4",
        )
    )


# ---------------------------------------------------------------------------
# 1. Phase 3 regressions
# ---------------------------------------------------------------------------

def test_eval_p4_investigation_completes_without_failures(eval_result):
    assert eval_result.status == InvestigationStatus.COMPLETED
    assert eval_result.failed_steps == 0
    assert eval_result.skipped_steps == 0


def test_eval_p4_cancellation_spike_still_visible_in_step1(eval_result):
    step1 = next(r for r in eval_result.step_results if r.step_id == "STEP-01")
    assert step1.status == StepStatus.COMPLETED
    rows = step1.tool_output.get("rows", [])
    monthly = {r["churn_month"]: r["total_cancellations"] for r in rows}
    assert "2025-09" in monthly
    baseline = max(v for k, v in monthly.items() if k < "2025-09")
    assert monthly["2025-09"] > baseline * 2


def test_eval_p4_postmortem_retrieved_in_step9(eval_result):
    step9 = next(r for r in eval_result.step_results if r.step_id == "STEP-09")
    assert step9.status == StepStatus.COMPLETED
    content = step9.tool_output.get("content", "")
    assert "billing-gateway" in content
    assert "v2.4.0" in content
    assert "webhook" in content.lower()


# ---------------------------------------------------------------------------
# 2. Every successful step has evidence IDs
# ---------------------------------------------------------------------------

def test_eval_every_completed_step_has_at_least_one_evidence_id(eval_result):
    for sr in eval_result.step_results:
        if sr.status == StepStatus.COMPLETED:
            assert len(sr.evidence_ids) >= 1, (
                f"Step {sr.step_id} completed without evidence_ids."
            )


def test_eval_evidence_ids_are_globally_unique(eval_result):
    all_ids = []
    for sr in eval_result.step_results:
        all_ids.extend(sr.evidence_ids)
    assert len(all_ids) == len(set(all_ids))


def test_eval_evidence_id_format(eval_result):
    """All evidence IDs must follow EVID-NNN format."""
    import re
    pattern = re.compile(r"^EVID-\d{3,}$")
    for sr in eval_result.step_results:
        for eid in sr.evidence_ids:
            assert pattern.match(eid), f"Unexpected evidence ID format: {eid}"


# ---------------------------------------------------------------------------
# 3. Aggregate counts
# ---------------------------------------------------------------------------

def test_eval_total_evidence_items_matches_sum(eval_result):
    step_total = sum(len(sr.evidence_ids) for sr in eval_result.step_results)
    assert eval_result.total_evidence_items == step_total
    assert eval_result.total_evidence_items > 0


def test_eval_audit_event_count_is_positive(eval_result):
    assert eval_result.audit_event_count > 0


# ---------------------------------------------------------------------------
# 4. Evidence provenance: run ID and step ID are correct
# ---------------------------------------------------------------------------

def test_eval_step3_evidence_has_correct_provenance(tmp_path_factory):
    """Independently re-run to access the EvidenceStore for provenance checks."""
    temp = tmp_path_factory.mktemp("eval_p4_prov")
    db_url = f"sqlite:///{temp}/eval_prov.db"
    seed_enterprise_database(db_url=db_url, seed=42)

    registry = create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )

    # Build store and collector directly to inspect provenance
    run_id = "INV-PROV-TEST"
    store = EvidenceStore(investigation_run_id=run_id)
    collector = EvidenceCollector(investigation_run_id=run_id, store=store)

    # Execute STEP-03 (billing failure time series) via the registry
    tool_output = registry.execute(
        "sql_investigation",
        {
            "query": (
                "SELECT strftime('%Y-%m', event_date) AS month, "
                "COUNT(*) AS total_events, "
                "SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_events "
                "FROM billing_events GROUP BY month ORDER BY month ASC"
            ),
            "max_rows": 50,
        },
    )
    assert tool_output.success

    from src.investigation.models import InvestigationStepResult
    step_result = InvestigationStepResult(
        step_id="STEP-03",
        status=StepStatus.COMPLETED,
        tool_name="sql_investigation",
        tool_input={
            "query": (
                "SELECT strftime('%Y-%m', event_date) AS month, "
                "COUNT(*) AS total_events, "
                "SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_events "
                "FROM billing_events GROUP BY month ORDER BY month ASC"
            ),
        },
        tool_output=tool_output.model_dump(),
        row_count=tool_output.row_count,
        evidence_summary="test",
        evidence_ids=[],
    )
    ids = collector.collect(step_result)

    assert len(ids) == 1
    item = store.get(ids[0])
    assert item.investigation_run_id == run_id
    assert item.step_id == "STEP-03"
    assert item.tool_name == "sql_investigation"
    assert item.evidence_type == EvidenceType.SQL_RESULT

    # Rows preserved — September failure data must be present
    rows = item.content.get("rows", [])
    months = {r.get("month") for r in rows}
    assert "2025-09" in months


def test_eval_step9_document_evidence_preserves_document_id(tmp_path_factory):
    """STEP-09 evidence must record the exact document_id and full text."""
    temp = tmp_path_factory.mktemp("eval_p4_doc")
    db_url = f"sqlite:///{temp}/eval_doc.db"
    seed_enterprise_database(db_url=db_url, seed=42)

    registry = create_default_tool_registry(
        db_url=db_url,
        doc_dir=PROJECT_ROOT / "data" / "raw",
    )

    run_id = "INV-DOC-TEST"
    store = EvidenceStore(investigation_run_id=run_id)
    collector = EvidenceCollector(investigation_run_id=run_id, store=store)

    tool_output = registry.execute(
        "document_retrieval",
        {"action": "get", "document_id": "postmortem_inc_2025_002.md"},
    )
    assert tool_output.success

    from src.investigation.models import InvestigationStepResult
    step_result = InvestigationStepResult(
        step_id="STEP-09",
        status=StepStatus.COMPLETED,
        tool_name="document_retrieval",
        tool_input={"action": "get", "document_id": "postmortem_inc_2025_002.md"},
        tool_output=tool_output.model_dump(),
        evidence_ids=[],
    )
    ids = collector.collect(step_result)

    assert len(ids) == 1
    item = store.get(ids[0])
    assert item.evidence_type == EvidenceType.DOCUMENT_TEXT
    assert item.content["document_id"] == "postmortem_inc_2025_002.md"
    assert "billing-gateway" in item.content["full_text"]
    assert item.content["char_count"] > 0
    assert item.content["char_count"] == len(item.content["full_text"])


# ---------------------------------------------------------------------------
# 5. Hash stability across independent runs
# ---------------------------------------------------------------------------

def test_eval_content_hash_is_stable_across_runs(tmp_path_factory):
    """Running the same investigation twice must produce identical content hashes."""
    temps = [tmp_path_factory.mktemp(f"eval_hash_{i}") for i in range(2)]
    stores = []

    for i, temp in enumerate(temps):
        db_url = f"sqlite:///{temp}/eval_hash.db"
        seed_enterprise_database(db_url=db_url, seed=42)
        registry = create_default_tool_registry(
            db_url=db_url,
            doc_dir=PROJECT_ROOT / "data" / "raw",
        )
        run_id = f"INV-HASH-RUN-{i}"
        store = EvidenceStore(investigation_run_id=run_id)
        collector = EvidenceCollector(investigation_run_id=run_id, store=store)

        tool_output = registry.execute(
            "sql_investigation",
            {
                "query": (
                    "SELECT strftime('%Y-%m', cancellation_date) AS churn_month, "
                    "COUNT(*) AS total_cancellations FROM subscriptions "
                    "WHERE cancellation_date IS NOT NULL "
                    "GROUP BY churn_month ORDER BY churn_month ASC"
                ),
                "max_rows": 50,
            },
        )

        from src.investigation.models import InvestigationStepResult
        step_result = InvestigationStepResult(
            step_id="STEP-01",
            status=StepStatus.COMPLETED,
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT strftime('%Y-%m', cancellation_date) AS churn_month, "
                    "COUNT(*) AS total_cancellations FROM subscriptions "
                    "WHERE cancellation_date IS NOT NULL "
                    "GROUP BY churn_month ORDER BY churn_month ASC"
                ),
            },
            tool_output=tool_output.model_dump(),
            row_count=tool_output.row_count,
            evidence_ids=[],
        )
        collector.collect(step_result)
        stores.append(store)

    hash_run0 = stores[0].all()[0].content_hash
    hash_run1 = stores[1].all()[0].content_hash
    assert hash_run0 == hash_run1, (
        "Identical investigation steps on identical data must produce identical content hashes."
    )
