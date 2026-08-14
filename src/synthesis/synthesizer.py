"""Investigation Synthesizer service.

Coordinates the end-to-end evidence-backed synthesis workflow:
  1. Build evidence-constrained prompt via PromptBuilder.
  2. Invoke LLMProvider (or MockLLMProvider).
  3. Parse raw generation into structured InvestigationReport.
  4. Validate all citations strictly via CitationValidator against the EvidenceStore.
  5. Record immutable audit events throughout the synthesis lifecycle.

The synthesizer is a pure, read-only consumer of previously collected evidence.
It never executes tools, SQL queries, or document access directly.
"""

import json
from typing import Optional
from src.investigation.audit import AuditEventType, AuditTrail
from src.investigation.evidence import EvidenceStore
from src.investigation.models import InvestigationPlan, InvestigationRunResult
from src.synthesis.models import InvestigationReport, SynthesisStatus
from src.synthesis.prompts import PromptBuilder
from src.synthesis.provider import LLMProvider, MockLLMProvider
from src.synthesis.validator import CitationValidator


class InvestigationSynthesizer:
    """Service orchestrating evidence-constrained investigation report synthesis."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        validator: Optional[CitationValidator] = None,
    ):
        self.provider: LLMProvider = provider or MockLLMProvider()
        self.validator: CitationValidator = validator or CitationValidator()

    def synthesize(
        self,
        question: str,
        investigation_run_id: str,
        store: EvidenceStore,
        plan: Optional[InvestigationPlan] = None,
        run_result: Optional[InvestigationRunResult] = None,
        audit: Optional[AuditTrail] = None,
    ) -> InvestigationReport:
        """Synthesize an evidence-grounded report from the given evidence store and context."""
        # 1. Audit: synthesis started
        if audit is not None:
            audit.record(
                AuditEventType.SYNTHESIS_STARTED,
                metadata={
                    "investigation_run_id": investigation_run_id,
                    "evidence_items_count": store.total_count,
                    "provider": type(self.provider).__name__,
                },
            )

        # 2. Build constrained prompt
        prompt = PromptBuilder.build_synthesis_prompt(
            question=question,
            investigation_run_id=investigation_run_id,
            store=store,
            plan=plan,
            run_result=run_result,
        )

        # 3. Generate response via LLM provider
        try:
            raw_response = self.provider.generate(prompt)
        except Exception as gen_err:
            error_report = InvestigationReport(
                investigation_run_id=investigation_run_id,
                question=question,
                executive_summary="Synthesis failed due to an unexpected provider generation error.",
                findings=[],
                root_cause=None,
                contributing_factors=[],
                recommendations=[],
                limitations=["Provider execution failed."],
                evidence_ids=[],
                citation_valid=False,
                synthesis_status=SynthesisStatus.ERROR,
                validation_errors=[f"Generation error: {str(gen_err)}"],
                metadata={"error": str(gen_err)},
            )
            if audit is not None:
                audit.record(
                    AuditEventType.SYNTHESIS_FAILED,
                    metadata={"error": str(gen_err), "reason": "generation_exception"},
                )
            return error_report

        # 4. Parse raw response into InvestigationReport
        try:
            # Clean possible markdown wrapping if any
            cleaned_json = raw_response.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            elif cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()

            parsed_data = json.loads(cleaned_json)
            report = InvestigationReport.model_validate(parsed_data)
        except Exception as parse_err:
            error_report = InvestigationReport(
                investigation_run_id=investigation_run_id,
                question=question,
                executive_summary="Synthesis failed: unable to parse provider output into valid report schema.",
                findings=[],
                root_cause=None,
                contributing_factors=[],
                recommendations=[],
                limitations=["Provider returned malformed JSON or invalid schema."],
                evidence_ids=[],
                citation_valid=False,
                synthesis_status=SynthesisStatus.ERROR,
                validation_errors=[f"Parsing error: {str(parse_err)}"],
                metadata={"raw_response": raw_response[:500]},
            )
            if audit is not None:
                audit.record(
                    AuditEventType.SYNTHESIS_FAILED,
                    metadata={"error": str(parse_err), "reason": "json_parse_error"},
                )
            return error_report

        # 5. Audit: synthesis generated
        if audit is not None:
            audit.record(
                AuditEventType.SYNTHESIS_GENERATED,
                metadata={
                    "findings_count": len(report.findings),
                    "recommendations_count": len(report.recommendations),
                    "root_cause_identified": report.root_cause is not None,
                },
            )

        # 6. Validate citations against EvidenceStore
        validation_result = self.validator.validate(report, store)

        # 7. Audit: synthesis validated or failed
        if audit is not None:
            if validation_result.is_valid:
                audit.record(
                    AuditEventType.SYNTHESIS_VALIDATED,
                    metadata={
                        "valid_citations_count": len(validation_result.valid_evidence_ids),
                        "findings_count": len(report.findings),
                    },
                )
            else:
                audit.record(
                    AuditEventType.SYNTHESIS_FAILED,
                    metadata={
                        "errors": validation_result.errors,
                        "invalid_citations": validation_result.invalid_evidence_ids,
                    },
                )

        return report
