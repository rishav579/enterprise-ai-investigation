"""Unit tests for the Phase 4 evidence domain model.

Covers:
  - EvidenceType taxonomy
  - compute_content_hash determinism and mutation sensitivity
  - EvidenceItem immutability (frozen=True)
  - EvidenceStore append-only semantics and queries
  - Typed content schemas
"""

import pytest
from src.investigation.evidence import (
    EvidenceItem,
    EvidenceStore,
    EvidenceType,
    SQLEvidenceContent,
    DocumentTextContent,
    DocumentMatchContent,
    DocumentListingContent,
    compute_content_hash,
)


# ---------------------------------------------------------------------------
# Helper to build a minimal EvidenceItem
# ---------------------------------------------------------------------------

def make_item(
    sequence_number: int = 1,
    step_id: str = "STEP-01",
    evidence_type: EvidenceType = EvidenceType.SQL_RESULT,
    content: dict | None = None,
) -> EvidenceItem:
    if content is None:
        content = {"rows": [{"col": "val"}], "row_count": 1, "columns": ["col"], "truncated": False, "query_reference": "SELECT 1"}
    ch = compute_content_hash(content)
    return EvidenceItem(
        evidence_id=f"EVID-{sequence_number:03d}",
        investigation_run_id="INV-UNIT-001",
        step_id=step_id,
        tool_name="sql_investigation",
        evidence_type=evidence_type,
        source_reference=f"sql_investigation:{step_id}",
        content=content,
        content_hash=ch,
        sequence_number=sequence_number,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Content hash tests
# ---------------------------------------------------------------------------

class TestComputeContentHash:
    def test_same_content_produces_same_hash(self):
        content = {"a": 1, "b": [2, 3], "c": "hello"}
        h1 = compute_content_hash(content)
        h2 = compute_content_hash(content)
        assert h1 == h2

    def test_different_content_produces_different_hash(self):
        h1 = compute_content_hash({"rows": [{"a": 1}]})
        h2 = compute_content_hash({"rows": [{"a": 2}]})
        assert h1 != h2

    def test_key_order_does_not_affect_hash(self):
        h1 = compute_content_hash({"b": 2, "a": 1})
        h2 = compute_content_hash({"a": 1, "b": 2})
        assert h1 == h2, "Hash must be order-independent (sort_keys=True)"

    def test_adding_field_changes_hash(self):
        base = {"rows": [{"x": 1}]}
        modified = {"rows": [{"x": 1}], "extra": True}
        assert compute_content_hash(base) != compute_content_hash(modified)

    def test_hash_is_hex_string_of_expected_length(self):
        h = compute_content_hash({"test": True})
        assert isinstance(h, str)
        assert len(h) == 64, "SHA-256 hex digest must be 64 characters"

    def test_empty_dict_has_stable_hash(self):
        h1 = compute_content_hash({})
        h2 = compute_content_hash({})
        assert h1 == h2

    def test_mutation_detection(self):
        """Simulates an evidence tampering attempt: hash must differ."""
        original = {"rows": [{"billing_failure_rate": 0.08}], "row_count": 1}
        tampered = {"rows": [{"billing_failure_rate": 0.02}], "row_count": 1}
        assert compute_content_hash(original) != compute_content_hash(tampered)


# ---------------------------------------------------------------------------
# EvidenceItem tests
# ---------------------------------------------------------------------------

class TestEvidenceItem:
    def test_evidence_item_created_successfully(self):
        item = make_item(sequence_number=1)
        assert item.evidence_id == "EVID-001"
        assert item.investigation_run_id == "INV-UNIT-001"
        assert item.evidence_type == EvidenceType.SQL_RESULT

    def test_evidence_item_is_frozen(self):
        """EvidenceItem must be immutable after construction."""
        item = make_item()
        with pytest.raises(Exception):
            item.evidence_id = "EVID-TAMPERED"

    def test_content_hash_matches_recomputation(self):
        """Hash stored on creation must match freshly recomputed hash."""
        item = make_item()
        recomputed = compute_content_hash(item.content)
        assert item.content_hash == recomputed

    def test_evidence_id_format(self):
        item = make_item(sequence_number=7)
        assert item.evidence_id == "EVID-007"


# ---------------------------------------------------------------------------
# EvidenceStore tests
# ---------------------------------------------------------------------------

class TestEvidenceStore:
    def test_store_starts_empty(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        assert store.total_count == 0
        assert store.all() == []

    def test_append_and_retrieve_by_id(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        item = make_item(sequence_number=1)
        store.append(item)
        assert store.get("EVID-001") is item

    def test_append_multiple_preserves_order(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        items = [make_item(seq, step_id=f"STEP-{seq:02d}") for seq in range(1, 5)]
        for item in items:
            store.append(item)
        assert store.all() == items

    def test_duplicate_id_raises_value_error(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        item = make_item(sequence_number=1)
        store.append(item)
        with pytest.raises(ValueError, match="already exists"):
            store.append(item)

    def test_get_nonexistent_returns_none(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        assert store.get("EVID-999") is None

    def test_for_step_filters_correctly(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        store.append(make_item(1, step_id="STEP-01"))
        store.append(make_item(2, step_id="STEP-02"))
        store.append(make_item(3, step_id="STEP-01"))

        step1_items = store.for_step("STEP-01")
        assert len(step1_items) == 2
        assert all(item.step_id == "STEP-01" for item in step1_items)

    def test_ids_for_step(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        store.append(make_item(1, step_id="STEP-03"))
        store.append(make_item(2, step_id="STEP-03"))
        assert store.ids_for_step("STEP-03") == ["EVID-001", "EVID-002"]

    def test_total_count_increments(self):
        store = EvidenceStore(investigation_run_id="INV-UNIT-001")
        assert store.total_count == 0
        store.append(make_item(1))
        assert store.total_count == 1
        store.append(make_item(2, step_id="STEP-02"))
        assert store.total_count == 2


# ---------------------------------------------------------------------------
# Typed content schema tests
# ---------------------------------------------------------------------------

class TestTypedEvidenceContentSchemas:
    def test_sql_evidence_content(self):
        content = SQLEvidenceContent(
            query_reference="SELECT COUNT(*) FROM subscriptions",
            columns=["count"],
            rows=[{"count": 150}],
            row_count=1,
            truncated=False,
        )
        dumped = content.model_dump()
        assert dumped["query_reference"] == "SELECT COUNT(*) FROM subscriptions"
        assert dumped["row_count"] == 1
        assert not dumped["truncated"]

    def test_document_text_content(self):
        content = DocumentTextContent(
            document_id="postmortem.md",
            full_text="# Postmortem\nRoot cause: webhook bug.",
            char_count=38,
        )
        assert content.document_id == "postmortem.md"
        assert "webhook" in content.full_text

    def test_document_match_content(self):
        content = DocumentMatchContent(
            document_id="runbook.md",
            line_number=42,
            excerpt="The billing-gateway webhook timed out",
            context_before="Previous line",
            context_after="Next line",
        )
        assert content.line_number == 42
        assert "billing-gateway" in content.excerpt

    def test_document_listing_content(self):
        content = DocumentListingContent(
            documents=[{"document_id": "doc1.md", "title": "Doc 1", "size_bytes": 1024}],
            document_count=1,
        )
        assert content.document_count == 1
        assert content.documents[0]["document_id"] == "doc1.md"
