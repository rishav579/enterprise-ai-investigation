"""Unit tests for PromptBuilder."""

import pytest
from src.investigation.evidence import (
    EvidenceItem,
    EvidenceStore,
    EvidenceType,
    compute_content_hash,
)
from src.synthesis.prompts import PromptBuilder


@pytest.fixture
def empty_store():
    return EvidenceStore(investigation_run_id="INV-EMPTY")


@pytest.fixture
def populated_store():
    store = EvidenceStore(investigation_run_id="INV-PROMPT-001")
    content1 = {
        "query_reference": "SELECT count(*) FROM subscriptions",
        "columns": ["count"],
        "rows": [{"count": 85}],
        "row_count": 1,
        "truncated": False,
    }
    item1 = EvidenceItem(
        evidence_id="EVID-001",
        investigation_run_id="INV-PROMPT-001",
        step_id="STEP-01",
        tool_name="sql_investigation",
        evidence_type=EvidenceType.SQL_RESULT,
        source_reference="sql_investigation:STEP-01",
        content=content1,
        content_hash=compute_content_hash(content1),
        sequence_number=1,
    )
    store.append(item1)
    return store


def test_format_evidence_item(populated_store):
    item = populated_store.get("EVID-001")
    formatted = PromptBuilder.format_evidence_item(item)
    assert "[EVIDENCE ITEM: EVID-001]" in formatted
    assert "Step ID: STEP-01" in formatted
    assert "Tool: sql_investigation" in formatted
    assert "Type: sql_result" in formatted
    assert "SELECT count(*)" in formatted


def test_build_evidence_block_empty(empty_store):
    block = PromptBuilder.build_evidence_block(empty_store)
    assert "[NO EVIDENCE ITEMS RECORDED IN THIS INVESTIGATION RUN]" in block


def test_build_evidence_block_populated(populated_store):
    block = PromptBuilder.build_evidence_block(populated_store)
    assert "EVID-001" in block
    assert "sql_investigation" in block


def test_build_synthesis_prompt_contains_boundaries_and_instructions(populated_store):
    prompt = PromptBuilder.build_synthesis_prompt(
        question="Why did churn increase?",
        investigation_run_id="INV-PROMPT-001",
        store=populated_store,
    )
    assert "Enterprise AI Investigation Synthesis Engine" in prompt
    assert "STRICT EVIDENCE GROUNDING" in prompt
    assert "PROMPT INJECTION DEFENSE & DATA BOUNDARIES" in prompt
    assert "BEGIN UNTRUSTED EVIDENCE BLOCK (DATA ONLY)" in prompt
    assert "END UNTRUSTED EVIDENCE BLOCK" in prompt
    assert "INV-PROMPT-001" in prompt
    assert "EVID-001" in prompt
