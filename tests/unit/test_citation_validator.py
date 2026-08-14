"""Unit tests for CitationValidator."""

import pytest
from src.investigation.evidence import (
    EvidenceItem,
    EvidenceStore,
    EvidenceType,
    compute_content_hash,
)
from src.synthesis.models import (
    ConfidenceLevel,
    Finding,
    InvestigationReport,
    PriorityLevel,
    Recommendation,
    SynthesisStatus,
)
from src.synthesis.validator import CitationValidator


@pytest.fixture
def run_a_store():
    store = EvidenceStore(investigation_run_id="INV-RUN-A")
    c1 = {"rows": [{"churn": 50}]}
    store.append(
        EvidenceItem(
            evidence_id="EVID-001",
            investigation_run_id="INV-RUN-A",
            step_id="STEP-01",
            tool_name="sql_investigation",
            evidence_type=EvidenceType.SQL_RESULT,
            source_reference="sql_investigation:STEP-01",
            content=c1,
            content_hash=compute_content_hash(c1),
            sequence_number=1,
        )
    )
    c2 = {"rows": [{"inc": "INC-001"}]}
    store.append(
        EvidenceItem(
            evidence_id="EVID-002",
            investigation_run_id="INV-RUN-A",
            step_id="STEP-02",
            tool_name="sql_investigation",
            evidence_type=EvidenceType.SQL_RESULT,
            source_reference="sql_investigation:STEP-02",
            content=c2,
            content_hash=compute_content_hash(c2),
            sequence_number=2,
        )
    )
    return store


@pytest.fixture
def run_b_store():
    store = EvidenceStore(investigation_run_id="INV-RUN-B")
    c1 = {"rows": [{"other": 999}]}
    store.append(
        EvidenceItem(
            evidence_id="EVID-001",
            investigation_run_id="INV-RUN-B",
            step_id="STEP-01",
            tool_name="sql_investigation",
            evidence_type=EvidenceType.SQL_RESULT,
            source_reference="sql_investigation:STEP-01",
            content=c1,
            content_hash=compute_content_hash(c1),
            sequence_number=1,
        )
    )
    return store


def test_valid_same_run_citations(run_a_store):
    report = InvestigationReport(
        investigation_run_id="INV-RUN-A",
        question="Why did churn increase?",
        executive_summary="Summary of findings based on evidence.",
        findings=[
            Finding(
                finding_id="FND-001",
                statement="Churn increased in September.",
                evidence_ids=["EVID-001"],
            ),
            Finding(
                finding_id="FND-002",
                statement="Incident occurred.",
                evidence_ids=["EVID-002"],
            ),
        ],
        recommendations=[
            Recommendation(
                recommendation_id="REC-001",
                action="Fix gateway",
                rationale="Root cause",
                evidence_ids=["EVID-002"],
            )
        ],
        evidence_ids=["EVID-001", "EVID-002"],
    )
    res = CitationValidator.validate(report, run_a_store)
    assert res.is_valid is True
    assert report.citation_valid is True
    assert report.synthesis_status == SynthesisStatus.SUCCESS
    assert report.validation_errors == []


def test_unknown_evidence_id_rejected(run_a_store):
    report = InvestigationReport(
        investigation_run_id="INV-RUN-A",
        question="Why did churn increase?",
        executive_summary="Summary of investigation findings.",
        findings=[
            Finding(
                finding_id="FND-001",
                statement="Fabricated finding citing non-existent evidence.",
                evidence_ids=["EVID-999"],  # Nonexistent!
            )
        ],
        evidence_ids=["EVID-999"],
    )
    res = CitationValidator.validate(report, run_a_store)
    assert res.is_valid is False
    assert report.citation_valid is False
    assert report.synthesis_status == SynthesisStatus.VALIDATION_FAILED
    assert any("EVID-999" in err for err in res.errors)
    assert "EVID-999" in res.invalid_evidence_ids


def test_cross_run_isolation_rejected(run_a_store, run_b_store):
    """Report from RUN-A attempting to validate against RUN-B's EvidenceStore."""
    report = InvestigationReport(
        investigation_run_id="INV-RUN-A",
        question="Question A",
        executive_summary="Summary of investigation A findings.",
        findings=[
            Finding(
                finding_id="FND-001",
                statement="Finding citing RUN-A evidence",
                evidence_ids=["EVID-002"],
            )
        ],
        evidence_ids=["EVID-002"],
    )
    # Validating report for RUN-A against store for RUN-B
    res = CitationValidator.validate(report, run_b_store)
    assert res.is_valid is False
    assert report.citation_valid is False
    assert any("Investigation Run ID mismatch" in err for err in res.errors)


def test_finding_without_evidence_rejected(run_a_store):
    report = InvestigationReport(
        investigation_run_id="INV-RUN-A",
        question="Why did churn increase?",
        executive_summary="Summary of investigation findings.",
        findings=[
            Finding(
                finding_id="FND-001",
                statement="Unsupported finding without citations.",
                evidence_ids=[],  # Empty!
            )
        ],
    )
    res = CitationValidator.validate(report, run_a_store)
    assert res.is_valid is False
    assert any("contains no cited evidence IDs" in err for err in res.errors)
