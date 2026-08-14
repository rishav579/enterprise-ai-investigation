"""Immutable audit trail for investigation runs.

Every significant event during an investigation is recorded as an AuditEvent.
Events are append-only — once recorded they cannot be mutated through the
public API.  This provides a complete, chronologically ordered record of
what happened, in what order, for each investigation run.

Sequence numbers are deterministic (monotonically increasing integers) so
the audit trail is fully reproducible in tests without depending on wall-clock
time.

Audit event types (AuditEventType) are a controlled vocabulary; new types may
be added but existing ones must not be renamed or removed once deployed.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Event type vocabulary
# ---------------------------------------------------------------------------

class AuditEventType(str, Enum):
    """Controlled vocabulary of investigation lifecycle events."""
    INVESTIGATION_STARTED        = "investigation_started"
    PLAN_CREATED                 = "plan_created"
    STEP_STARTED                 = "step_started"
    STEP_COMPLETED               = "step_completed"
    STEP_FAILED                  = "step_failed"
    STEP_BLOCKED                 = "step_blocked"
    EVIDENCE_COLLECTED           = "evidence_collected"
    INVESTIGATION_COMPLETED      = "investigation_completed"
    INVESTIGATION_FAILED         = "investigation_failed"
    INVESTIGATION_PARTIAL        = "investigation_partial"


# ---------------------------------------------------------------------------
# AuditEvent — a single immutable event record
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    """A single immutable audit event in the investigation lifecycle."""
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(
        ...,
        description="Stable unique identifier in AUDIT-NNN format (sequence within the run)",
    )
    investigation_run_id: str = Field(
        ...,
        description="ID of the investigation run this event belongs to",
    )
    event_type: AuditEventType = Field(
        ...,
        description="Controlled vocabulary event type",
    )
    sequence_number: int = Field(
        ...,
        description="Monotonically increasing sequence number (1-based) within the run",
    )
    step_id: Optional[str] = Field(
        None,
        description="Investigation step ID, when the event relates to a specific step",
    )
    tool_name: Optional[str] = Field(
        None,
        description="Tool name, when the event relates to a tool execution",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence IDs collected, populated on EVIDENCE_COLLECTED events",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured context for the event",
    )


# ---------------------------------------------------------------------------
# AuditTrail — append-only ordered log
# ---------------------------------------------------------------------------

class AuditTrail:
    """Append-only ordered log of AuditEvents for one investigation run.

    Events are stored in sequence number order.  Once recorded, events
    cannot be mutated or removed through the public API.

    Sequence numbers start at 1 and increment by 1 for each recorded event.
    """

    def __init__(self, investigation_run_id: str):
        self._run_id: str = investigation_run_id
        self._events: List[AuditEvent] = []
        self._next_seq: int = 1

    # ------------------------------------------------------------------
    # Recording events
    # ------------------------------------------------------------------

    def record(
        self,
        event_type: AuditEventType,
        *,
        step_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Record a new audit event and return it."""
        seq = self._next_seq
        event = AuditEvent(
            event_id=f"AUDIT-{seq:03d}",
            investigation_run_id=self._run_id,
            event_type=event_type,
            sequence_number=seq,
            step_id=step_id,
            tool_name=tool_name,
            evidence_ids=list(evidence_ids) if evidence_ids else [],
            metadata=dict(metadata) if metadata else {},
        )
        self._events.append(event)
        self._next_seq += 1
        return event

    # ------------------------------------------------------------------
    # Read access
    # ------------------------------------------------------------------

    def all(self) -> List[AuditEvent]:
        """Return all events in sequence order (returns a defensive copy)."""
        return list(self._events)

    def for_step(self, step_id: str) -> List[AuditEvent]:
        """Return all events related to a specific step, in sequence order."""
        return [e for e in self._events if e.step_id == step_id]

    def of_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        """Return all events of a specific type, in sequence order."""
        return [e for e in self._events if e.event_type == event_type]

    @property
    def total_count(self) -> int:
        """Total number of recorded events."""
        return len(self._events)

    @property
    def investigation_run_id(self) -> str:
        return self._run_id
