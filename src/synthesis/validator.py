"""Deterministic citation validator for investigation reports."""

from dataclasses import dataclass, field
from typing import List, Set
from src.investigation.evidence import EvidenceStore
from src.synthesis.models import InvestigationReport, SynthesisStatus


@dataclass
class CitationValidationResult:
    """Detailed outcome of validating report citations against the EvidenceStore."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    valid_evidence_ids: List[str] = field(default_factory=list)
    invalid_evidence_ids: List[str] = field(default_factory=list)


class CitationValidator:
    """Validates that all evidence citations in an InvestigationReport belong strictly

    to the corresponding investigation run's EvidenceStore.
    """

    @classmethod
    def validate(
        cls,
        report: InvestigationReport,
        store: EvidenceStore,
    ) -> CitationValidationResult:
        """Validate all citations in the report against the provided EvidenceStore.

        Mutates report in-place by setting citation_valid, validation_errors, and synthesis_status.
        """
        errors: List[str] = []
        valid_ids: List[str] = []
        invalid_ids: List[str] = []

        # 1. Verify Investigation Run ID matches
        if report.investigation_run_id != store.investigation_run_id:
            msg = (
                f"Investigation Run ID mismatch: report specifies '{report.investigation_run_id}' "
                f"but EvidenceStore belongs to '{store.investigation_run_id}'."
            )
            errors.append(msg)

        # Build set of all known valid evidence IDs for this store
        known_evidence_map = {item.evidence_id: item for item in store.all()}
        known_eids: Set[str] = set(known_evidence_map.keys())

        # 2. Validate Findings
        for finding in report.findings:
            if not finding.evidence_ids:
                errors.append(
                    f"Finding '{finding.finding_id}' contains no cited evidence IDs."
                )
            for eid in finding.evidence_ids:
                if eid in known_eids:
                    # Check foreign run guard
                    item = known_evidence_map[eid]
                    if item.investigation_run_id != store.investigation_run_id:
                        errors.append(
                            f"Finding '{finding.finding_id}' cites foreign run evidence ID '{eid}' "
                            f"(originates from '{item.investigation_run_id}')."
                        )
                        invalid_ids.append(eid)
                    else:
                        valid_ids.append(eid)
                else:
                    errors.append(
                        f"Finding '{finding.finding_id}' cites nonexistent evidence ID '{eid}'."
                    )
                    invalid_ids.append(eid)

        # 3. Validate Recommendations
        for rec in report.recommendations:
            for eid in rec.evidence_ids:
                if eid in known_eids:
                    item = known_evidence_map[eid]
                    if item.investigation_run_id != store.investigation_run_id:
                        errors.append(
                            f"Recommendation '{rec.recommendation_id}' cites foreign run evidence ID '{eid}'."
                        )
                        invalid_ids.append(eid)
                    else:
                        valid_ids.append(eid)
                else:
                    errors.append(
                        f"Recommendation '{rec.recommendation_id}' cites nonexistent evidence ID '{eid}'."
                    )
                    invalid_ids.append(eid)

        # 4. Validate top-level evidence_ids list
        for eid in report.evidence_ids:
            if eid not in known_eids:
                errors.append(f"Top-level evidence list cites nonexistent evidence ID '{eid}'.")
                invalid_ids.append(eid)
            else:
                valid_ids.append(eid)

        # Determine overall validity
        is_valid = len(errors) == 0

        # Update report state
        report.citation_valid = is_valid
        report.validation_errors = errors
        if not is_valid:
            if report.synthesis_status != SynthesisStatus.INSUFFICIENT_EVIDENCE:
                report.synthesis_status = SynthesisStatus.VALIDATION_FAILED

        # Clean duplicates in result lists
        unique_valid = list(dict.fromkeys(valid_ids))
        unique_invalid = list(dict.fromkeys(invalid_ids))

        return CitationValidationResult(
            is_valid=is_valid,
            errors=errors,
            valid_evidence_ids=unique_valid,
            invalid_evidence_ids=unique_invalid,
        )
