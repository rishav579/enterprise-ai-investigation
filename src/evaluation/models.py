"""Domain models for Phase 6 evaluation and hardening."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ExpectedSecurityBehavior(str, Enum):
    ALLOWED = "allowed"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    TREATED_AS_DATA = "treated_as_data"

class ExpectedSignal(BaseModel):
    """Semantic expected signal from a tool execution or evidence."""
    model_config = ConfigDict(frozen=True)
    description: str
    tool_name: Optional[str] = None
    evidence_type: Optional[str] = None
    must_be_present: bool = True
    matching_keywords: List[str] = Field(default_factory=list)

class GoldenScenario(BaseModel):
    """A deterministic investigation scenario with ground truth."""
    scenario_id: str
    question: str
    scenario_type: str  # e.g., 'churn', 'security', 'insufficient'
    expected_signals: List[ExpectedSignal] = Field(default_factory=list)
    expected_root_cause_keywords: List[str] = Field(default_factory=list)
    expect_insufficient_evidence: bool = False
    expected_security_behavior: Optional[ExpectedSecurityBehavior] = None

class MetricResult(BaseModel):
    name: str
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvaluationCaseResult(BaseModel):
    scenario_id: str
    passed: bool
    failure_reasons: List[str] = Field(default_factory=list)
    metrics: List[MetricResult] = Field(default_factory=list)
    run_id: str

class EvaluationSummary(BaseModel):
    dataset_version: str = "v1"
    timestamp: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_results: List[EvaluationCaseResult] = Field(default_factory=list)
    aggregate_metrics: Dict[str, float] = Field(default_factory=dict)
