"""Automated offline evaluation runner for the Enterprise AI Investigation System."""

import time
import json
import uuid
from typing import Dict, Any, List

from src.evaluation.models import (
    GoldenScenario,
    ExpectedSignal,
    ExpectedSecurityBehavior,
    EvaluationCaseResult,
    MetricResult,
    EvaluationSummary,
)
from src.investigation.orchestrator import InvestigationOrchestrator
from src.investigation.models import InvestigationRequest, StepStatus
from src.synthesis.synthesizer import InvestigationSynthesizer
from src.synthesis.provider import MockLLMProvider
from src.synthesis.models import SynthesisStatus
from src.tools.registry import ToolRegistry


class EvaluationRunner:
    """Runs the golden dataset through the investigation and synthesis stack."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.orchestrator = InvestigationOrchestrator(registry=registry)
        self.synthesizer = InvestigationSynthesizer(provider=MockLLMProvider())

    def evaluate_scenario(self, scenario: GoldenScenario) -> EvaluationCaseResult:
        """Run a single scenario and evaluate the results against ground truth."""
        run_id = f"EVAL-{scenario.scenario_id}-{uuid.uuid4().hex[:6]}"
        request = InvestigationRequest(
            question=scenario.question,
            investigation_id=run_id
        )

        run_result, store, audit = self.orchestrator.run_with_context(request)
        
        # Verify Audit Trail Integrity
        from src.evaluation.audit_verifier import AuditVerifier
        is_audit_valid, audit_errors = AuditVerifier.verify(audit)
        if not is_audit_valid:
            return EvaluationCaseResult(
                scenario_id=scenario.scenario_id,
                passed=False,
                failure_reasons=[f"Audit Verification Failed: {err}" for err in audit_errors],
                metrics=[],
                run_id=run_id
            )

        # Synthesize report
        report = self.synthesizer.synthesize(
            question=request.question,
            investigation_run_id=run_id,
            store=store,
            plan=run_result.plan,
            run_result=run_result,
            audit=audit
        )

        passed = True
        failure_reasons = []
        metrics: List[MetricResult] = []

        # 1. Evaluate Guardrails / Security Behavior
        if scenario.expected_security_behavior:
            if scenario.expected_security_behavior == ExpectedSecurityBehavior.BLOCKED:
                # We expect at least one step to have failed due to security limits
                security_blocked = any(
                    step.status == StepStatus.FAILED and (
                        "Prohibited" in str(step.error_message) or 
                        "forbidden" in str(step.error_message) or 
                        "Strict path boundary" in str(step.error_message) or
                        "Multiple SQL statements" in str(step.error_message)
                    )
                    for step in run_result.step_results
                )
                if not security_blocked:
                    passed = False
                    failure_reasons.append("Expected security block did not occur.")
                
                # If blocked, we shouldn't necessarily care about normal signals
                return EvaluationCaseResult(
                    scenario_id=scenario.scenario_id,
                    passed=passed,
                    failure_reasons=failure_reasons,
                    metrics=metrics,
                    run_id=run_id
                )

        # 2. Evaluate Insufficient Evidence
        if scenario.expect_insufficient_evidence:
            if report.synthesis_status != SynthesisStatus.INSUFFICIENT_EVIDENCE:
                passed = False
                failure_reasons.append(f"Expected INSUFFICIENT_EVIDENCE, got {report.synthesis_status.value}.")
            if report.root_cause is not None:
                passed = False
                failure_reasons.append("Report contained a root cause when evidence was insufficient.")
                
            return EvaluationCaseResult(
                scenario_id=scenario.scenario_id,
                passed=passed,
                failure_reasons=failure_reasons,
                metrics=metrics,
                run_id=run_id
            )

        # 3. Evaluate Expected Signals (Recall)
        if scenario.expected_signals:
            matched_signals = 0
            for expected in scenario.expected_signals:
                signal_matched = False
                
                # Check if the signal keywords were found in the evidence store contents or step inputs
                for step in run_result.step_results:
                    if expected.tool_name and step.tool_name != expected.tool_name:
                        continue
                    
                    # Combine step input and output strings for matching
                    content_str = str(step.tool_input).lower() + " " + str(step.tool_output).lower()
                    
                    # Check all keywords
                    keywords_found = [kw.lower() in content_str for kw in expected.matching_keywords]
                    if keywords_found and all(keywords_found):
                        signal_matched = True
                        break
                        
                if signal_matched:
                    matched_signals += 1
                elif expected.must_be_present:
                    passed = False
                    failure_reasons.append(f"Missing expected signal: {expected.description}")
            
            recall = matched_signals / len(scenario.expected_signals)
            metrics.append(MetricResult(name="evidence_recall", value=recall))

        # 4. Evaluate Synthesis Result (Root Cause Keywords)
        if scenario.expected_root_cause_keywords and passed:
            if not report.root_cause:
                passed = False
                failure_reasons.append("Missing root cause in synthesis.")
            else:
                rc_lower = report.root_cause.lower()
                matched_rc = 0
                for kw in scenario.expected_root_cause_keywords:
                    if kw.lower() in rc_lower:
                        matched_rc += 1
                    else:
                        passed = False
                        failure_reasons.append(f"Root cause missing expected keyword: {kw}")
                
                rc_precision = matched_rc / len(scenario.expected_root_cause_keywords)
                metrics.append(MetricResult(name="root_cause_precision", value=rc_precision))

        return EvaluationCaseResult(
            scenario_id=scenario.scenario_id,
            passed=passed,
            failure_reasons=failure_reasons,
            metrics=metrics,
            run_id=run_id
        )

    def run_all(self, dataset: List[GoldenScenario]) -> EvaluationSummary:
        """Run all scenarios and produce a summary."""
        results = []
        total = len(dataset)
        passed = 0
        failed = 0

        for scenario in dataset:
            res = self.evaluate_scenario(scenario)
            results.append(res)
            if res.passed:
                passed += 1
            else:
                failed += 1

        # Calculate aggregates
        sum_recall = sum(
            m.value for r in results for m in r.metrics if m.name == "evidence_recall"
        )
        sum_precision = sum(
            m.value for r in results for m in r.metrics if m.name == "root_cause_precision"
        )
        count_recall = sum(1 for r in results for m in r.metrics if m.name == "evidence_recall")
        count_precision = sum(1 for r in results for m in r.metrics if m.name == "root_cause_precision")

        aggregates = {}
        if count_recall > 0:
            aggregates["mean_evidence_recall"] = sum_recall / count_recall
        if count_precision > 0:
            aggregates["mean_root_cause_precision"] = sum_precision / count_precision

        return EvaluationSummary(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            case_results=results,
            aggregate_metrics=aggregates
        )
