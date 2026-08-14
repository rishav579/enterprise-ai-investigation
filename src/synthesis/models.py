"""Pydantic domain models for investigation synthesis and reporting."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConfidenceLevel(str, Enum):
    """Confidence level in an investigation finding."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PriorityLevel(str, Enum):
    """Priority level for an investigation recommendation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SynthesisStatus(str, Enum):
    """Lifecycle/validation status of the synthesized investigation report."""
    SUCCESS = "success"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    VALIDATION_FAILED = "validation_failed"
    ERROR = "error"


class Finding(BaseModel):
    """A distinct factual finding backed by explicit evidence IDs."""
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        ...,
        description="Unique identifier for the finding (e.g., 'FND-001')",
    )
    statement: str = Field(
        ...,
        min_length=5,
        description="Factual finding statement grounded strictly in evidence",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of cited evidence IDs (e.g. ['EVID-001', 'EVID-003'])",
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.HIGH,
        description="Confidence level for this finding based on supporting evidence strength",
    )


class Recommendation(BaseModel):
    """An actionable operational recommendation linked to supporting evidence."""
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(
        ...,
        description="Unique identifier for the recommendation (e.g., 'REC-001')",
    )
    action: str = Field(
        ...,
        min_length=5,
        description="Specific recommended operational or engineering action",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Rationale explaining why this action is recommended",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Supporting evidence IDs for the recommendation",
    )
    priority: PriorityLevel = Field(
        default=PriorityLevel.HIGH,
        description="Priority level for executing this recommendation",
    )


class InvestigationReport(BaseModel):
    """Structured, evidence-grounded investigation report."""
    model_config = ConfigDict(extra="forbid")

    investigation_run_id: str = Field(
        ...,
        description="Identifier of the investigation run that produced the evidence",
    )
    question: str = Field(
        ...,
        description="Original business investigation question",
    )
    executive_summary: str = Field(
        ...,
        min_length=10,
        description="Executive summary synthesizing the investigation conclusions",
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="Ordered list of evidence-backed findings",
    )
    root_cause: Optional[str] = Field(
        None,
        description="Identified primary root cause, or None if evidence is insufficient",
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="List of secondary or contributing factors identified from evidence",
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Ordered list of actionable recommendations",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit limitations, data gaps, or uncertainties",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="All distinct evidence IDs referenced throughout this report",
    )
    citation_valid: bool = Field(
        default=False,
        description="Whether all cited evidence IDs were verified against the EvidenceStore",
    )
    synthesis_status: SynthesisStatus = Field(
        default=SynthesisStatus.SUCCESS,
        description="Status of the synthesis and citation validation",
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Detailed citation validation errors if citation_valid is False",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional synthesis metadata (provider name, model, prompt version, etc.)",
    )
