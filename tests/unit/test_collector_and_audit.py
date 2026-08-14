"""Unit tests for EvidenceCollector and AuditTrail."""

import pytest
from src.investigation.audit import AuditEventType, AuditTrail
from src.investigation.collector import EvidenceCollector
from src.investigation.evidence import EvidenceStore, EvidenceType, EvidenceType as ET
from src.investigation.models import InvestigationStepResult, StepStatus

# Alias for convenience
DOCUMENT_SEARCH_SUMMARY = EvidenceType.DOCUMENT_SEARCH_SUMMARY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sql_step_result(
    step_id: str = "STEP-01",
    rows: list | None = None,
    columns: list | None = None,
    row_count: int | None = None,
    success: bool = True,
    status: StepStatus = StepStatus.COMPLETED,
) -> InvestigationStepResult:
    if rows is None:
        rows = [{"churn_month": "2025-09", "total_cancellations": 82}]
    if columns is None:
        columns = ["churn_month", "total_cancellations"]
    if row_count is None:
        row_count = len(rows)

    return InvestigationStepResult(
        step_id=step_id,
        status=status,
        tool_name="sql_investigation",
        tool_input={"query": "SELECT churn_month, total_cancellations FROM v", "max_rows": 50},
        tool_output={
            "success": success,
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "truncated": False,
            "error": None,
        },
        evidence_summary="SQL query returned 1 row(s).",
        evidence_ids=[],
    )


def make_doc_text_step_result(step_id: str = "STEP-09") -> InvestigationStepResult:
    return InvestigationStepResult(
        step_id=step_id,
        status=StepStatus.COMPLETED,
        tool_name="document_retrieval",
        tool_input={"action": "get", "document_id": "postmortem_inc_2025_002.md"},
        tool_output={
            "success": True,
            "action": "get",
            "documents": [],
            "content": "# Postmortem\nbilling-gateway webhook bug v2.4.0.",
            "matches": [],
            "total_matches": 0,
            "error": None,
        },
        evidence_summary="Retrieved document.",
        evidence_ids=[],
    )


def make_doc_search_step_result(
    step_id: str = "STEP-08",
    match_count: int = 2,
) -> InvestigationStepResult:
    matches = [
        {
            "document_id": "postmortem_inc_2025_002.md",
            "line_number": i + 1,
            "excerpt": f"billing-gateway line {i + 1}",
            "context_before": None,
            "context_after": None,
        }
        for i in range(match_count)
    ]
    return InvestigationStepResult(
        step_id=step_id,
        status=StepStatus.COMPLETED,
        tool_name="document_retrieval",
        tool_input={"action": "search", "query": "billing-gateway webhook", "max_results": 10},
        tool_output={
            "success": True,
            "action": "search",
            "documents": [],
            "content": None,
            "matches": matches,
            "total_matches": match_count,
            "error": None,
        },
        evidence_summary="Search found 2 matching excerpt(s).",
        evidence_ids=[],
    )


def make_doc_list_step_result(step_id: str = "STEP-XX") -> InvestigationStepResult:
    return InvestigationStepResult(
        step_id=step_id,
        status=StepStatus.COMPLETED,
        tool_name="document_retrieval",
        tool_input={"action": "list"},
        tool_output={
            "success": True,
            "action": "list",
            "documents": [
                {"document_id": "doc1.md", "title": "Doc 1", "size_bytes": 1024, "relative_path": "doc1.md"},
            ],
            "content": None,
            "matches": [],
            "total_matches": 0,
            "error": None,
        },
        evidence_summary="Listed 1 document(s).",
        evidence_ids=[],
    )


# ---------------------------------------------------------------------------
# EvidenceCollector tests
# ---------------------------------------------------------------------------

class TestEvidenceCollector:
    def _make_collector(self, run_id: str = "INV-COL-001"):
        store = EvidenceStore(investigation_run_id=run_id)
        collector = EvidenceCollector(investigation_run_id=run_id, store=store)
        return collector, store

    def test_sql_success_produces_one_sql_result_evidence(self):
        collector, store = self._make_collector()
        ids = collector.collect(make_sql_step_result())
        assert len(ids) == 1
        assert ids[0] == "EVID-001"
        item = store.get("EVID-001")
        assert item.evidence_type == EvidenceType.SQL_RESULT

    def test_sql_evidence_preserves_query_and_rows(self):
        collector, store = self._make_collector()
        step_result = make_sql_step_result(
            rows=[{"month": "2025-09", "count": 82}],
            columns=["month", "count"],
        )
        collector.collect(step_result)
        item = store.get("EVID-001")
        assert item.content["query_reference"] == step_result.tool_input["query"]
        assert item.content["rows"] == [{"month": "2025-09", "count": 82}]
        assert item.content["columns"] == ["month", "count"]
        assert item.content["row_count"] == 1

    def test_failed_step_produces_no_evidence(self):
        collector, store = self._make_collector()
        failed_result = make_sql_step_result(status=StepStatus.FAILED)
        ids = collector.collect(failed_result)
        assert ids == []
        assert store.total_count == 0

    def test_blocked_step_produces_no_evidence(self):
        collector, store = self._make_collector()
        blocked = InvestigationStepResult(
            step_id="STEP-08",
            status=StepStatus.BLOCKED,
            tool_name="document_retrieval",
            tool_input={},
            tool_output=None,
            error_message="Step blocked: deps not met",
            evidence_ids=[],
        )
        ids = collector.collect(blocked)
        assert ids == []
        assert store.total_count == 0

    def test_document_get_produces_document_text_evidence(self):
        collector, store = self._make_collector()
        ids = collector.collect(make_doc_text_step_result())
        assert len(ids) == 1
        item = store.get("EVID-001")
        assert item.evidence_type == EvidenceType.DOCUMENT_TEXT
        assert item.content["document_id"] == "postmortem_inc_2025_002.md"
        assert "webhook" in item.content["full_text"]

    def test_document_search_produces_summary_plus_match_items(self):
        collector, store = self._make_collector()
        ids = collector.collect(make_doc_search_step_result(match_count=3))
        # 1 summary + 3 match items = 4 total
        assert len(ids) == 4
        # First item is the search summary
        summary = store.get(ids[0])
        assert summary.evidence_type == EvidenceType.DOCUMENT_SEARCH_SUMMARY
        assert summary.content["total_matches"] == 3
        # Remaining items are per-match
        for eid in ids[1:]:
            item = store.get(eid)
            assert item.evidence_type == EvidenceType.DOCUMENT_MATCH

    def test_document_search_evidence_preserves_line_number(self):
        collector, store = self._make_collector()
        collector.collect(make_doc_search_step_result(match_count=1))
        # ids[0] = search summary, ids[1] = first match
        match_item = next(i for i in store.all() if i.evidence_type == EvidenceType.DOCUMENT_MATCH)
        assert match_item.content["line_number"] == 1
        assert "billing-gateway" in match_item.content["excerpt"]

    def test_document_list_produces_listing_evidence(self):
        collector, store = self._make_collector()
        ids = collector.collect(make_doc_list_step_result())
        assert len(ids) == 1
        item = store.get("EVID-001")
        assert item.evidence_type == EvidenceType.DOCUMENT_LISTING
        assert item.content["document_count"] == 1

    def test_evidence_ids_are_unique_across_steps(self):
        collector, store = self._make_collector()
        ids_step1 = collector.collect(make_sql_step_result(step_id="STEP-01"))
        ids_step3 = collector.collect(make_sql_step_result(step_id="STEP-03"))
        all_ids = ids_step1 + ids_step3
        assert len(all_ids) == len(set(all_ids)), "Evidence IDs must be globally unique"

    def test_evidence_ids_are_sequential(self):
        collector, store = self._make_collector()
        collector.collect(make_sql_step_result(step_id="STEP-01"))
        collector.collect(make_sql_step_result(step_id="STEP-03"))
        ids = [item.evidence_id for item in store.all()]
        assert ids == ["EVID-001", "EVID-002"]

    def test_evidence_points_to_correct_run_id(self):
        collector, store = self._make_collector(run_id="INV-RUN-XYZ")
        collector.collect(make_sql_step_result())
        item = store.get("EVID-001")
        assert item.investigation_run_id == "INV-RUN-XYZ"

    def test_evidence_points_to_correct_step_id(self):
        collector, store = self._make_collector()
        collector.collect(make_sql_step_result(step_id="STEP-03"))
        item = store.get("EVID-001")
        assert item.step_id == "STEP-03"

    def test_evidence_points_to_correct_tool(self):
        collector, store = self._make_collector()
        collector.collect(make_sql_step_result())
        item = store.get("EVID-001")
        assert item.tool_name == "sql_investigation"

    def test_evidence_content_hash_is_stable(self):
        """Same SQL result must always produce the same content hash."""
        from src.investigation.evidence import compute_content_hash
        collector1, store1 = self._make_collector(run_id="INV-A")
        collector2, store2 = self._make_collector(run_id="INV-B")

        step = make_sql_step_result()
        collector1.collect(step)
        collector2.collect(step)

        hash1 = store1.get("EVID-001").content_hash
        hash2 = store2.get("EVID-001").content_hash
        assert hash1 == hash2, "Identical evidence content must produce identical hash"

    def test_modified_evidence_content_produces_different_hash(self):
        from src.investigation.evidence import compute_content_hash
        collector, store = self._make_collector()
        step_a = make_sql_step_result(rows=[{"count": 82}])
        step_b = make_sql_step_result(rows=[{"count": 99}])  # tampered value

        collector.collect(step_a)
        collector.collect(step_b)

        hash_a = store.get("EVID-001").content_hash
        hash_b = store.get("EVID-002").content_hash
        assert hash_a != hash_b

    def test_no_fabricated_evidence_when_tool_output_is_none(self):
        collector, store = self._make_collector()
        result = InvestigationStepResult(
            step_id="STEP-01",
            status=StepStatus.COMPLETED,
            tool_name="sql_investigation",
            tool_input={},
            tool_output=None,   # completed but no output (shouldn't happen in practice)
            evidence_ids=[],
        )
        ids = collector.collect(result)
        assert ids == []


# ---------------------------------------------------------------------------
# AuditTrail tests
# ---------------------------------------------------------------------------

class TestAuditTrail:
    def test_audit_trail_starts_empty(self):
        trail = AuditTrail("INV-AUDIT-001")
        assert trail.total_count == 0

    def test_record_event_returns_audit_event(self):
        trail = AuditTrail("INV-AUDIT-001")
        event = trail.record(AuditEventType.INVESTIGATION_STARTED, metadata={"q": "test"})
        assert event.event_type == AuditEventType.INVESTIGATION_STARTED
        assert event.event_id == "AUDIT-001"
        assert event.sequence_number == 1

    def test_sequence_numbers_are_monotonically_increasing(self):
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(AuditEventType.INVESTIGATION_STARTED)
        trail.record(AuditEventType.PLAN_CREATED)
        trail.record(AuditEventType.STEP_STARTED, step_id="STEP-01")
        events = trail.all()
        seqs = [e.sequence_number for e in events]
        assert seqs == [1, 2, 3]

    def test_events_cannot_be_mutated(self):
        """AuditEvent must be frozen/immutable."""
        trail = AuditTrail("INV-AUDIT-001")
        event = trail.record(AuditEventType.INVESTIGATION_STARTED)
        with pytest.raises(Exception):
            event.event_type = AuditEventType.INVESTIGATION_COMPLETED

    def test_all_returns_events_in_sequence_order(self):
        trail = AuditTrail("INV-AUDIT-001")
        types = [
            AuditEventType.INVESTIGATION_STARTED,
            AuditEventType.PLAN_CREATED,
            AuditEventType.STEP_STARTED,
            AuditEventType.STEP_COMPLETED,
            AuditEventType.INVESTIGATION_COMPLETED,
        ]
        for t in types:
            trail.record(t)
        recorded_types = [e.event_type for e in trail.all()]
        assert recorded_types == types

    def test_for_step_filters_by_step_id(self):
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(AuditEventType.STEP_STARTED, step_id="STEP-01")
        trail.record(AuditEventType.STEP_STARTED, step_id="STEP-02")
        trail.record(AuditEventType.STEP_COMPLETED, step_id="STEP-01")
        step1_events = trail.for_step("STEP-01")
        assert len(step1_events) == 2
        assert all(e.step_id == "STEP-01" for e in step1_events)

    def test_of_type_filters_by_event_type(self):
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(AuditEventType.STEP_STARTED, step_id="STEP-01")
        trail.record(AuditEventType.STEP_FAILED, step_id="STEP-02")
        trail.record(AuditEventType.STEP_STARTED, step_id="STEP-03")
        started = trail.of_type(AuditEventType.STEP_STARTED)
        assert len(started) == 2

    def test_evidence_ids_recorded_in_evidence_collected_event(self):
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(
            AuditEventType.EVIDENCE_COLLECTED,
            step_id="STEP-03",
            evidence_ids=["EVID-004", "EVID-005"],
        )
        events = trail.of_type(AuditEventType.EVIDENCE_COLLECTED)
        assert events[0].evidence_ids == ["EVID-004", "EVID-005"]

    def test_all_returns_defensive_copy(self):
        """Mutating the returned list must not corrupt internal state."""
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(AuditEventType.INVESTIGATION_STARTED)
        events_copy = trail.all()
        events_copy.clear()
        assert trail.total_count == 1  # internal state unchanged

    def test_metadata_is_stored_on_event(self):
        trail = AuditTrail("INV-AUDIT-001")
        trail.record(
            AuditEventType.INVESTIGATION_STARTED,
            metadata={"question": "Why did churn spike?"},
        )
        event = trail.all()[0]
        assert event.metadata["question"] == "Why did churn spike?"
