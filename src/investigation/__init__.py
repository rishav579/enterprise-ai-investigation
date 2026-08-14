"""Investigation planning, orchestration, evidence collection, and audit trail package."""

from src.investigation.models import (
    InvestigationRequest,
    InvestigationPlan,
    InvestigationStep,
    InvestigationStepResult,
    InvestigationRunResult,
    InvestigationStatus,
    StepStatus,
)
from src.investigation.planner import InvestigationPlanner
from src.investigation.orchestrator import InvestigationOrchestrator

# Phase 4
from src.investigation.evidence import (
    EvidenceType,
    EvidenceItem,
    EvidenceStore,
    SQLEvidenceContent,
    DocumentTextContent,
    DocumentMatchContent,
    DocumentListingContent,
    DocumentSearchSummaryContent,
    compute_content_hash,
)
from src.investigation.collector import EvidenceCollector
from src.investigation.audit import AuditEventType, AuditEvent, AuditTrail

__all__ = [
    # Phase 3
    "InvestigationRequest",
    "InvestigationPlan",
    "InvestigationStep",
    "InvestigationStepResult",
    "InvestigationRunResult",
    "InvestigationStatus",
    "StepStatus",
    "InvestigationPlanner",
    "InvestigationOrchestrator",
    # Phase 4 — evidence
    "EvidenceType",
    "EvidenceItem",
    "EvidenceStore",
    "SQLEvidenceContent",
    "DocumentTextContent",
    "DocumentMatchContent",
    "DocumentListingContent",
    "compute_content_hash",
    "EvidenceCollector",
    # Phase 4 — audit
    "AuditEventType",
    "AuditEvent",
    "AuditTrail",
]
