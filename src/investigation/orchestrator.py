"""Investigation Orchestrator.

Accepts an InvestigationRequest, obtains a structured InvestigationPlan from the
planner, then executes each step through the existing ToolRegistry in dependency
order.  All tool calls go strictly through the registry — no direct tool
instantiation or arbitrary execution.

Design constraints:
- Deterministic: same request → same execution sequence
- No LLM calls in this phase
- No subprocess / shell access
- No filesystem access outside the document tool
- Steps with failed dependencies are marked BLOCKED, not executed
- A failed step does not abort the entire investigation
"""

from typing import Any, Dict, Optional, Set
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


class InvestigationOrchestrator:
    """Executes a structured investigation plan step-by-step through the ToolRegistry.

    All tool access goes through the provided ToolRegistry instance.
    """

    def __init__(self, registry: ToolRegistry, planner: Optional[InvestigationPlanner] = None):
        self.registry = registry
        self.planner = planner or InvestigationPlanner()

    def run(self, request: InvestigationRequest) -> InvestigationRunResult:
        """Run a full investigation: plan → execute steps → collect results."""
        # 1. Build the investigation plan
        try:
            plan: InvestigationPlan = self.planner.plan(request)
        except Exception as plan_err:
            # Planning itself failed; return immediately with error
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
            )

        # 2. Execute steps in declared order, tracking completion states
        step_results: list[InvestigationStepResult] = []
        completed_step_ids: Set[str] = set()
        failed_step_ids: Set[str] = set()

        completed_count = 0
        failed_count = 0
        skipped_count = 0

        for step in plan.steps:
            # Dependency check: any required dependency not completed → BLOCKED
            unmet_deps = [
                dep for dep in step.depends_on
                if dep not in completed_step_ids
            ]
            if unmet_deps:
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
                    )
                )
                failed_step_ids.add(step.step_id)
                skipped_count += 1
                continue

            # Execute the step through the ToolRegistry
            try:
                tool_output = self.registry.execute(step.tool_name, step.tool_input)
            except KeyError as key_err:
                # Tool not registered
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=None,
                        error_message=str(key_err),
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue
            except Exception as exec_err:
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=None,
                        error_message=f"Unexpected execution error: {exec_err}",
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue

            # Evaluate success/failure from tool output
            tool_success = getattr(tool_output, "success", False)
            tool_error = getattr(tool_output, "error", None)

            if not tool_success:
                step_results.append(
                    InvestigationStepResult(
                        step_id=step.step_id,
                        status=StepStatus.FAILED,
                        tool_name=step.tool_name,
                        tool_input=step.tool_input,
                        tool_output=tool_output.model_dump(),
                        error_message=tool_error or "Tool returned success=False",
                    )
                )
                failed_step_ids.add(step.step_id)
                failed_count += 1
                continue

            # Step succeeded
            row_count = getattr(tool_output, "row_count", None)
            summary = _summarize_tool_output(step, tool_output)

            step_results.append(
                InvestigationStepResult(
                    step_id=step.step_id,
                    status=StepStatus.COMPLETED,
                    tool_name=step.tool_name,
                    tool_input=step.tool_input,
                    tool_output=tool_output.model_dump(),
                    row_count=row_count,
                    evidence_summary=summary,
                )
            )
            completed_step_ids.add(step.step_id)
            completed_count += 1

        # 3. Determine overall investigation status
        if failed_count == 0 and skipped_count == 0:
            overall_status = InvestigationStatus.COMPLETED
        elif completed_count == 0:
            overall_status = InvestigationStatus.FAILED
        else:
            overall_status = InvestigationStatus.PARTIAL

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
        )
