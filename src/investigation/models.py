"""Pydantic models for investigation planning and orchestration."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StepStatus(str, Enum):
    """Lifecycle state of an individual investigation step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"   # dependency failed → step cannot execute


class InvestigationStatus(str, Enum):
    """Overall state of an investigation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"   # some steps failed/skipped
    FAILED = "failed"


class InvestigationRequest(BaseModel):
    """Input payload for requesting an investigation."""
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Business investigation question (e.g. 'Why did churn spike in September?')",
    )
    investigation_id: str = Field(
        default_factory=lambda: f"INV-{uuid.uuid4().hex[:8].upper()}",
        description="Unique investigation run identifier",
    )
    scenario_hint: Optional[str] = Field(
        None,
        description="Optional hint for selecting the investigation scenario (e.g. 'churn_spike')",
    )
    max_steps: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of steps the plan may contain",
    )


class InvestigationStep(BaseModel):
    """A single planned step in the investigation."""
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., description="Unique step identifier within this investigation (e.g. STEP-01)")
    objective: str = Field(..., description="What this step aims to establish or answer")
    rationale: str = Field(..., description="Why this step is necessary for the investigation")
    tool_name: str = Field(..., description="Name of the registered tool to invoke for this step")
    tool_input: Dict[str, Any] = Field(..., description="Input payload to pass directly to the tool")
    expected_evidence_type: str = Field(
        ...,
        description="Type of evidence this step should produce (e.g. 'time_series_data', 'document_excerpt')",
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="step_ids that must complete successfully before this step can execute",
    )


class InvestigationPlan(BaseModel):
    """Structured investigation plan containing ordered, dependency-linked steps."""

    plan_id: str = Field(..., description="Unique plan identifier")
    investigation_id: str = Field(..., description="Parent investigation ID")
    question: str = Field(..., description="Original business question being investigated")
    scenario: str = Field(..., description="Named investigation scenario detected by planner")
    steps: List[InvestigationStep] = Field(..., min_length=1, description="Ordered investigation steps")
    total_steps: int = Field(..., description="Total number of planned steps")


class InvestigationStepResult(BaseModel):
    """Structured result captured from a single executed investigation step."""

    step_id: str = Field(..., description="Step identifier this result corresponds to")
    status: StepStatus = Field(..., description="Execution status")
    tool_name: str = Field(..., description="Tool that was invoked")
    tool_input: Dict[str, Any] = Field(..., description="Exact input passed to the tool")
    tool_output: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured tool result payload (matches tool's output schema)",
    )
    error_message: Optional[str] = Field(None, description="Error detail if status is FAILED or BLOCKED")
    row_count: Optional[int] = Field(None, description="Number of rows returned (SQL steps only)")
    evidence_summary: Optional[str] = Field(
        None,
        description="Human-readable summary of key evidence found in this step",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="IDs of EvidenceItems collected from this step (e.g. ['EVID-001', 'EVID-002'])",
    )


class InvestigationRunResult(BaseModel):
    """Final structured result for a complete investigation run."""

    investigation_id: str = Field(..., description="Unique investigation identifier")
    question: str = Field(..., description="Original business question")
    status: InvestigationStatus = Field(..., description="Overall investigation outcome")
    plan: InvestigationPlan = Field(..., description="The investigation plan that was executed")
    step_results: List[InvestigationStepResult] = Field(
        default_factory=list,
        description="Ordered list of step execution results",
    )
    total_steps: int = Field(..., description="Total steps in the plan")
    completed_steps: int = Field(0, description="Steps that completed successfully")
    failed_steps: int = Field(0, description="Steps that encountered errors")
    skipped_steps: int = Field(0, description="Steps that were blocked or explicitly skipped")
    error_message: Optional[str] = Field(
        None,
        description="Top-level error message if the investigation itself could not proceed",
    )
    # Phase 4: evidence and audit
    total_evidence_items: int = Field(
        0,
        description="Total number of evidence items collected across all steps",
    )
    audit_event_count: int = Field(
        0,
        description="Total number of audit events recorded during this run",
    )
