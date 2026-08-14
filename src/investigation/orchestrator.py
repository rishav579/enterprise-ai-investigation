"""Investigation Orchestrator — Phase 4: Evidence Collection & Audit Trail.

Extends the Phase 3 orchestrator with:
  - An EvidenceCollector that captures typed evidence from each successful step.
  - An AuditTrail that records every significant lifecycle event in sequence.
  - evidence_ids attached to each InvestigationStepResult.
  - total_evidence_items and audit_event_count in InvestigationRunResult.

All Phase 3 behaviour is preserved:
  - Deterministic: same request → same execution sequence.
  - Execution exclusively via ToolRegistry.
  - Declared step order respected.
  - Dependency tracking: BLOCKED on unmet deps.
  - Failed steps do not abort independent steps.
  - Existing result model fields remain unchanged.

No LLM calls are made.  Evidence collection is downstream of controlled tool
execution and is completely offline.
"""

from typing import Any, List, Optional, Set

from src.investigation.audit import AuditEventType, AuditTrail
from src.investigation.collector import EvidenceCollector
from src.investigation.evidence import EvidenceStore
from src.investigation.models import (
    InvestigationPlan,
    InvestigationRequest,
    InvestigationRunResult,
    InvestigationStatus,
    InvestigationStep,
    InvestigationStepResult,
    StepStatus,
)
from src.investigation.planner import InvestigationPlanner
from src.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Utility: step summary (unchanged from Phase 3)
# ---------------------------------------------------------------------------

def _summarize_tool_output(step: InvestigationStep, output: Any) -> str:
    """Produce a short human-readable summary of a tool result for quick scanning."""
    tool_name = step.tool_name
    try:
        if tool_name == "sql_investigation":
            row_count = getattr(output, "row_count", 0)
            truncated = getattr(output, "truncated", False)
            trunc_note = " (truncated)" if truncated else ""
            return f"SQL query returned {row_count} row(s){trunc_note}."
        elif tool_name == "document_retrieval":
            action = getattr(output, "action", "")
            if action == "list":
                count = len(getattr(output, "documents", []))
                return f"Listed {count} document(s) in knowledge base."
            elif action == "search":
                count = getattr(output, "total_matches", 0)
                return f"Search found {count} matching excerpt(s)."
            elif action == "get":
                content = getattr(output, "content", "")
                preview = content[:120].replace("\n", " ").strip() if content else "(empty)"
                return f"Retrieved document ({len(content)} chars). Preview: {preview}..."
        return f"Tool '{tool_name}' completed."
    except Exception:
        return f"Tool '{tool_name}' completed."


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class InvestigationOrchestrator:
    """Executes a structured investigation plan, collects evidence, and records audit events.

    All tool access goes through the provided ToolRegistry instance.
    Evidence collection goes through the EvidenceCollector (always downstream of tools).
    Audit events are recorded for every significant lifecycle transition.
    """

    def __init__(self, registry: ToolRegistry, planner: Optional[InvestigationPlanner] = None):
        self.registry = registry
        self.planner = planner or InvestigationPlanner()
        self.last_store: Optional[EvidenceStore] = None
        self.last_audit: Optional[AuditTrail] = None

    def run(
        self,
        request: InvestigationRequest,
        store: Optional[EvidenceStore] = None,
        audit: Optional[AuditTrail] = None,
    ) -> InvestigationRunResult:
        """Run a full investigation: plan → execute → collect evidence → audit."""
        # Initialise per-run evidence store and audit trail if not provided
        store = store or EvidenceStore(investigation_run_id=request.investigation_id)
        audit = audit or AuditTrail(investigation_run_id=request.investigation_id)
        self.last_store = store
        self.last_audit = audit

        collector = EvidenceCollector(
            investigation_run_id=request.investigation_id,
            store=store,
        )

        # Audit: investigation started
        audit.record(
            AuditEventType.INVESTIGATION_STARTED,
            metadata={"question": request.question},
        )

        # 1. Build the investigation plan
        try:
            plan: InvestigationPlan = self.planner.plan(request)
        except Exception as plan_err:
            audit.record(
                AuditEventType.INVESTIGATION_FAILED,
                metadata={"reason": f"Planning failed: {plan_err}"},
            )
            return InvestigationRunResult(
                investigation_id=request.investigation_id,
                question=request.question,
                status=InvestigationStatus.FAILED,
                plan=InvestigationPlan(
                    plan_id="PLAN-ERROR",
                    investigation_id=request.investigation_id,
                    question=request.question,
                    scenario="unknown",
                    steps=[],
                    total_steps=0,
                ),
                step_results=[],
                total_steps=0,
                completed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error_message=f"Planning failed: {plan_err}",
                total_evidence_items=0,
                audit_event_count=audit.total_count,
            )

        # Audit: plan created
        audit.record(
            AuditEventType.PLAN_CREATED,
            metadata={
                "plan_id": plan.plan_id,
                "scenario": plan.scenario,
                "total_steps": plan.total_steps,
            },
        )

        # 2. Execute steps in declared order, tracking completion states
        step_results: List[InvestigationStepResult] = []
        completed_step_ids: Set[str] = set()
        failed_step_ids: Set[str] = set()

        completed_count = 0
        failed_count = 0
        skipped_count = 0

        for step in plan.steps:
            # ---- Dependency check ----
            unmet_deps = [
                dep for dep in step.depends_on
                if dep not in completed_step_ids
            ]
            if unmet_deps:
                audit.record(
                    AuditEventType.STEP_BLOCKED,
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    metadata={"unmet_dependencies": unmet_deps},
                )
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.BLOCKED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=None,
                        error_message=(
                            f"Step blocked: required dependencies not completed: {unmet_deps}"
                        ),
                        evidence_summary=None,
                        evidence_ids=[],
                    )
                )
                failed_step_ids.add(step.step_id)
                skipped_count += 1
                continue

            # ---- Step started ----
            audit.record(
                AuditEventType.STEP_STARTED,
                step_id=step.step_id,
                tool_name=step.tool_name,
            )

            # ---- Execute via ToolRegistry ----
            try:
                tool_output = self.registry.execute(step.tool_name, step.tool_input)
            except KeyError as key_err:
                audit.record(
                    AuditEventType.STEP_FAILED,
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    metadata={"error": str(key_err), "reason": "tool_not_registered"},
                )
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=None,
                        error_message=str(key_err),
                        evidence_ids=[],
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue
            except Exception as exec_err:
                audit.record(
                    AuditEventType.STEP_FAILED,
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    metadata={"error": str(exec_err), "reason": "unexpected_error"},
                )
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=None,
                        error_message=f"Unexpected execution error: {exec_err}",
                        evidence_ids=[],
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue

            # ---- Evaluate tool success ----
            tool_success = getattr(tool_output, "success", False)
            tool_error = getattr(tool_output, "error", None)

            if not tool_success:
                audit.record(
                    AuditEventType.STEP_FAILED,
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    metadata={
                        "error": tool_error or "Tool returned success=False",
                        "reason": "tool_reported_failure",
                    },
                )
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=tool_output.model_dump(),
                        error_message=tool_error or "Tool returned success=False",
                        evidence_ids=[],
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue

            # ---- Step succeeded: collect evidence ----
            step_result_partial = InvestigationStepResult(
                step_id=step.step_id,
                status=StepStatus.COMPLETED,
                tool_name=step.tool_name,
                tool_input=step.tool_input,
                tool_output=tool_output.model_dump(),
                row_count=getattr(tool_output, "row_count", None),
                evidence_summary=_summarize_tool_output(step, tool_output),
                evidence_ids=[],  # placeholder; filled below
            )

            collected_ids = collector.collect(step_result_partial)

            if collected_ids:
                audit.record(
                    AuditEventType.EVIDENCE_COLLECTED,
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    evidence_ids=collected_ids,
                    metadata={"evidence_count": len(collected_ids)},
                )

            # Rebuild with filled evidence_ids (model is not frozen)
            step_result_final = InvestigationStepResult(
                step_id=step.step_id,
                status=StepStatus.COMPLETED,
                tool_name=step.tool_name,
                tool_input=step.tool_input,
                tool_output=tool_output.model_dump(),
                row_count=getattr(tool_output, "row_count", None),
                evidence_summary=step_result_partial.evidence_summary,
                evidence_ids=collected_ids,
            )

            audit.record(
                AuditEventType.STEP_COMPLETED,
                step_id=step.step_id,
                tool_name=step.tool_name,
                metadata={"evidence_count": len(collected_ids)},
            )

            step_results.append(step_result_final)
            completed_step_ids.add(step.step_id)
            completed_count += 1

        # 3. Determine overall investigation status
        if failed_count == 0 and skipped_count == 0:
            overall_status = InvestigationStatus.COMPLETED
        elif completed_count == 0:
            overall_status = InvestigationStatus.FAILED
        else:
            overall_status = InvestigationStatus.PARTIAL

        # Audit: investigation outcome
        final_event_type = {
            InvestigationStatus.COMPLETED: AuditEventType.INVESTIGATION_COMPLETED,
            InvestigationStatus.PARTIAL:   AuditEventType.INVESTIGATION_PARTIAL,
            InvestigationStatus.FAILED:    AuditEventType.INVESTIGATION_FAILED,
        }.get(overall_status, AuditEventType.INVESTIGATION_COMPLETED)

        audit.record(
            final_event_type,
            metadata={
                "completed_steps": completed_count,
                "failed_steps": failed_count,
                "skipped_steps": skipped_count,
                "total_evidence_items": store.total_count,
            },
        )

        return InvestigationRunResult(
            investigation_id=request.investigation_id,
            question=request.question,
            status=overall_status,
            plan=plan,
            step_results=step_results,
            total_steps=plan.total_steps,
            completed_steps=completed_count,
            failed_steps=failed_count,
            skipped_steps=skipped_count,
            total_evidence_items=store.total_count,
            audit_event_count=audit.total_count,
        )

    def run_with_context(
        self,
        request: InvestigationRequest,
    ) -> tuple[InvestigationRunResult, EvidenceStore, AuditTrail]:
        """Convenience method that returns the run result alongside the EvidenceStore and AuditTrail."""
        store = EvidenceStore(investigation_run_id=request.investigation_id)
        audit = AuditTrail(investigation_run_id=request.investigation_id)
        result = self.run(request, store=store, audit=audit)
        return result, store, audit
