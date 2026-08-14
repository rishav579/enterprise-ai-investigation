"""Verification tools for the immutable audit trail."""

from typing import List, Tuple
from src.investigation.audit import AuditTrail, AuditEventType


class AuditVerificationError(Exception):
    """Raised when an audit trail fails verification constraints."""
    pass


class AuditVerifier:
    """Verifies the integrity and sequential coherence of an AuditTrail."""

    @staticmethod
    def verify(audit_trail: AuditTrail) -> Tuple[bool, List[str]]:
        """
        Verify the audit trail for:
        1. Exact sequential sequence numbers (1, 2, 3...)
        2. Correct string formatting of event IDs (AUDIT-001, etc.)
        3. Mandatory start/end lifecycle events.
        
        Returns (is_valid, list_of_errors).
        """
        errors = []
        events = audit_trail.all()
        
        if not events:
            return False, ["Audit trail is completely empty."]

        # 1. Sequence numbering and Event IDs
        expected_seq = 1
        for event in events:
            if event.sequence_number != expected_seq:
                errors.append(
                    f"Sequence gap/mismatch: expected {expected_seq}, got {event.sequence_number} "
                    f"for event {event.event_id}"
                )
            
            expected_id = f"AUDIT-{expected_seq:03d}"
            if event.event_id != expected_id:
                errors.append(
                    f"Event ID mismatch: expected '{expected_id}', got '{event.event_id}'"
                )
                
            expected_seq += 1

        # 2. Lifecycle constraints
        first_event = events[0]
        if first_event.event_type != AuditEventType.INVESTIGATION_STARTED:
            errors.append(
                f"Invalid start event: expected {AuditEventType.INVESTIGATION_STARTED.value}, "
                f"got {first_event.event_type.value}"
            )
            
        terminal_events = {
            AuditEventType.INVESTIGATION_COMPLETED,
            AuditEventType.INVESTIGATION_FAILED,
            AuditEventType.INVESTIGATION_PARTIAL,
            AuditEventType.SYNTHESIS_FAILED,
            AuditEventType.SYNTHESIS_VALIDATED,
            AuditEventType.SYNTHESIS_GENERATED,
        }
        
        last_event = events[-1]
        if last_event.event_type not in terminal_events:
            errors.append(
                f"Invalid end event: '{last_event.event_type.value}' is not a recognized terminal state."
            )

        # 3. Check for evidence collection without step completion
        # If EVIDENCE_COLLECTED is recorded, it must be preceded by STEP_STARTED for that step
        step_starts = set()
        for event in events:
            if event.event_type == AuditEventType.STEP_STARTED and event.step_id:
                step_starts.add(event.step_id)
            elif event.event_type == AuditEventType.EVIDENCE_COLLECTED and event.step_id:
                if event.step_id not in step_starts:
                    errors.append(f"Evidence collected for step {event.step_id} which never started.")

        return len(errors) == 0, errors
