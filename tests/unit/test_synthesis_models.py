"""Unit tests for Phase 5 synthesis domain models."""

import pytest
from pydantic import ValidationError
from src.synthesis.models import (
    ConfidenceLevel,
    Finding,
    InvestigationReport,
    PriorityLevel,
    Recommendation,
    SynthesisStatus,
)


def test_finding_model_valid():
    finding = Finding(
        finding_id="FND-001",
        statement="Customer cancellations spiked by 400% in September 2025.",
        evidence_ids=["EVID-001", "EVID-002"],
        confidence=ConfidenceLevel.HIGH,
    )
    assert finding.finding_id == "FND-001"
    assert len(finding.evidence_ids) == 2
    assert finding.confidence == ConfidenceLevel.HIGH


def test_finding_model_extra_forbid():
    with pytest.raises(ValidationError):
        Finding(
            finding_id="FND-001",
            statement="Valid statement here",
            evidence_ids=["EVID-001"],
            unknown_field="not allowed",
        )


def test_recommendation_model_valid():
    rec = Recommendation(
        recommendation_id="REC-001",
        action="Deploy hotfix v2.4.1 to restore webhook confirmation handling.",
        rationale="Prevents legitimate payments from being marked as failed.",
        evidence_ids=["EVID-006", "EVID-009"],
        priority=PriorityLevel.CRITICAL,
    )
    assert rec.recommendation_id == "REC-001"
    assert rec.priority == PriorityLevel.CRITICAL


def test_recommendation_model_extra_forbid():
    with pytest.raises(ValidationError):
        Recommendation(
            recommendation_id="REC-001",
            action="Action statement",
            rationale="Rationale statement",
            extra_field="rejected",
        )


def test_investigation_report_model_defaults():
    report = InvestigationReport(
        investigation_run_id="INV-TEST-001",
        question="Why did churn spike?",
        executive_summary="Executive summary synthesizing the investigation findings.",
        findings=[
            Finding(
                finding_id="FND-001",
                statement="Cancellations increased in September.",
                evidence_ids=["EVID-001"],
            )
        ],
    )
    assert report.citation_valid is False
    assert report.synthesis_status == SynthesisStatus.SUCCESS
    assert report.root_cause is None
    assert report.recommendations == []
    assert report.validation_errors == []
