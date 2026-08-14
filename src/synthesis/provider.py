"""Provider abstraction for investigation synthesis LLMs."""

import abc
import json
import re
from typing import Any, Dict, List, Optional
from src.synthesis.models import (
    ConfidenceLevel,
    Finding,
    InvestigationReport,
    PriorityLevel,
    Recommendation,
    SynthesisStatus,
)


class LLMProvider(abc.ABC):
    """Abstract interface for LLM synthesis providers."""

    @abc.abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a raw text response (expected JSON string) from the prompt."""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic, offline mock LLM provider for investigation report synthesis.

    Synthesizes evidence-grounded reports by parsing the structured evidence items
    delimited in the prompt. It strictly obeys data boundaries, resists prompt injection
    in evidence text, and handles insufficient evidence gracefully.
    """

    def __init__(self, custom_response_json: Optional[str] = None):
        self._custom_response = custom_response_json

    def set_custom_response(self, response_json: Optional[str]) -> None:
        """Override output with a custom JSON string for testing error/edge cases."""
        self._custom_response = response_json

    def generate(self, prompt: str) -> str:
        """Generate deterministic JSON report from evidence in the prompt."""
        if self._custom_response is not None:
            return self._custom_response

        # Extract context from prompt
        run_id_match = re.search(r"Investigation Run ID:\s*([^\n\r]+)", prompt)
        run_id = run_id_match.group(1).strip() if run_id_match else "INV-UNKNOWN"

        question_match = re.search(r"Business Question:\s*([^\n\r]+)", prompt)
        question = question_match.group(1).strip() if question_match else "Investigation Question"

        # Check for empty/insufficient evidence
        if "[NO EVIDENCE ITEMS RECORDED IN THIS INVESTIGATION RUN]" in prompt:
            empty_report = {
                "investigation_run_id": run_id,
                "question": question,
                "executive_summary": "Insufficient evidence was gathered during this investigation run to reach any factual conclusions.",
                "findings": [],
                "root_cause": None,
                "contributing_factors": [],
                "recommendations": [],
                "limitations": [
                    "No evidence items were recorded in this investigation run.",
                    "Unable to verify root cause or operational contributing factors."
                ],
                "evidence_ids": [],
                "citation_valid": False,
                "synthesis_status": SynthesisStatus.INSUFFICIENT_EVIDENCE.value,
                "validation_errors": [],
                "metadata": {"provider": "MockLLMProvider", "mode": "insufficient_evidence"}
            }
            return json.dumps(empty_report)

        # Extract all available evidence items from prompt
        evidence_map: Dict[str, Dict[str, Any]] = {}
        parts = prompt.split("--- [EVIDENCE ITEM:")
        for part in parts[1:]:
            header_end = part.find("] ---")
            if header_end == -1:
                continue
            eid = part[:header_end].strip()
            rest = part[header_end + 5:]

            step_id_match = re.search(r"Step ID:\s*([^\r\n]+)", rest)
            tool_match = re.search(r"Tool:\s*([^\r\n]+)", rest)
            type_match = re.search(r"Type:\s*([^\r\n]+)", rest)
            source_match = re.search(r"Source Reference:\s*([^\r\n]+)", rest)
            content_start = rest.find("Content:")

            step_id = step_id_match.group(1).strip() if step_id_match else ""
            tool = tool_match.group(1).strip() if tool_match else ""
            ev_type = type_match.group(1).strip() if type_match else ""
            source_ref = source_match.group(1).strip() if source_match else ""

            parsed_content = {}
            if content_start != -1:
                content_str = rest[content_start + 8:].strip()
                next_delim = content_str.find("==================================================")
                if next_delim != -1:
                    content_str = content_str[:next_delim].strip()
                try:
                    parsed_content = json.loads(content_str)
                except Exception:
                    first_brace = content_str.find("{")
                    last_brace = content_str.rfind("}")
                    if first_brace != -1 and last_brace != -1:
                        try:
                            parsed_content = json.loads(content_str[first_brace:last_brace+1])
                        except Exception:
                            parsed_content = {}

            evidence_map[eid] = {
                "evidence_id": eid,
                "step_id": step_id,
                "tool": tool,
                "type": ev_type,
                "source_ref": source_ref,
                "content": parsed_content,
            }

        # If no evidence parsed from blocks
        if not evidence_map:
            # Fallback check if simple IDs appear
            found_eids = re.findall(r"\[EVIDENCE ITEM:\s*(EVID-\d+)\]", prompt)
            if not found_eids:
                empty_report = {
                    "investigation_run_id": run_id,
                    "question": question,
                    "executive_summary": "No structured evidence items could be extracted from the investigation run.",
                    "findings": [],
                    "root_cause": None,
                    "contributing_factors": [],
                    "recommendations": [],
                    "limitations": ["No valid evidence items available."],
                    "evidence_ids": [],
                    "citation_valid": False,
                    "synthesis_status": SynthesisStatus.INSUFFICIENT_EVIDENCE.value,
                    "validation_errors": [],
                    "metadata": {"provider": "MockLLMProvider", "mode": "insufficient_evidence"}
                }
                return json.dumps(empty_report)

        # Generate findings based on available evidence items
        findings: List[Dict[str, Any]] = []
        recommendations: List[Dict[str, Any]] = []
        contributing_factors: List[str] = []
        all_used_eids: List[str] = []
        root_cause: Optional[str] = None

        # Look for specific evidence types/steps
        for eid, ev in evidence_map.items():
            content = ev["content"]
            ev_type = ev["type"]
            step_id = ev["step_id"]

            if ev_type == "sql_result":
                rows = content.get("rows", [])
                query_ref = content.get("query_reference", "").lower()

                # Step 1 / Churn spike
                if "cancellation" in query_ref or "churn_month" in str(rows):
                    sept_rows = [r for r in rows if r.get("churn_month") == "2025-09"]
                    if sept_rows:
                        findings.append({
                            "finding_id": f"FND-{len(findings)+1:03d}",
                            "statement": f"Customer cancellations spiked significantly in September 2025 (reaching {sept_rows[0].get('total_cancellations', 'high')} cancellations compared to baseline).",
                            "evidence_ids": [eid],
                            "confidence": ConfidenceLevel.HIGH.value,
                        })
                        all_used_eids.append(eid)

                # Step 2 / Segment breakdown
                elif "plan" in query_ref and "region" in query_ref:
                    findings.append({
                        "finding_id": f"FND-{len(findings)+1:03d}",
                        "statement": "Cancellations disproportionately affected Pro and Enterprise customer tiers across EU-Central and US-East regions.",
                        "evidence_ids": [eid],
                        "confidence": ConfidenceLevel.HIGH.value,
                    })
                    contributing_factors.append("Concentration of cancellations in Pro/Enterprise plans in EU-Central and US-East.")
                    all_used_eids.append(eid)

                # Step 3 / Billing failures
                elif "billing_events" in query_ref or "failure_rate_pct" in str(rows):
                    findings.append({
                        "finding_id": f"FND-{len(findings)+1:03d}",
                        "statement": "Billing transaction failures surged from sub-3% baseline to over 30% in September 2025.",
                        "evidence_ids": [eid],
                        "confidence": ConfidenceLevel.HIGH.value,
                    })
                    contributing_factors.append("Systemic surge in payment transaction failures during the anomaly window.")
                    all_used_eids.append(eid)

                # Step 5 / Support SLA
                elif "support_tickets" in query_ref or "ticket_month" in str(rows):
                    findings.append({
                        "finding_id": f"FND-{len(findings)+1:03d}",
                        "statement": "Support queue resolution times degraded dramatically (exceeding 40+ hours) due to high volume of billing disputes.",
                        "evidence_ids": [eid],
                        "confidence": ConfidenceLevel.HIGH.value,
                    })
                    contributing_factors.append("Support queue backlog delaying resolution of erroneous account locks.")
                    all_used_eids.append(eid)

                # Step 6 / Product incidents
                elif "product_incidents" in query_ref:
                    p1_incidents = [r for r in rows if r.get("severity") == "P1"]
                    if p1_incidents:
                        findings.append({
                            "finding_id": f"FND-{len(findings)+1:03d}",
                            "statement": "A P1 incident (INC-2025-002) occurred on the billing-gateway service on 2025-09-05, misclassifying successful payments as failed.",
                            "evidence_ids": [eid],
                            "confidence": ConfidenceLevel.HIGH.value,
                        })
                        all_used_eids.append(eid)

                # Step 7 / Release events
                elif "release_events" in query_ref:
                    v24_releases = [r for r in rows if "2.4.0" in str(r.get("version", ""))]
                    if v24_releases:
                        findings.append({
                            "finding_id": f"FND-{len(findings)+1:03d}",
                            "statement": "Software release v2.4.0 was deployed to the billing-gateway service immediately preceding the incident spike.",
                            "evidence_ids": [eid],
                            "confidence": ConfidenceLevel.HIGH.value,
                        })
                        all_used_eids.append(eid)

            elif ev_type == "document_text":
                full_text = content.get("full_text", "")
                if "billing-gateway" in full_text and "webhook" in full_text.lower():
                    findings.append({
                        "finding_id": f"FND-{len(findings)+1:03d}",
                        "statement": "Internal postmortem INC-2025-002 confirms the webhook confirmation logic in billing-gateway v2.4.0 failed to parse payment status properly.",
                        "evidence_ids": [eid],
                        "confidence": ConfidenceLevel.HIGH.value,
                    })
                    all_used_eids.append(eid)
                    root_cause = "Deployment of billing-gateway v2.4.0 introduced a webhook parsing regression that erroneously marked legitimate customer transactions as failed, triggering automatic subscription cancellations."

        # If findings were created for the cancellation scenario
        if findings and root_cause:
            # Build recommendations backed by evidence
            pm_eids = [eid for eid, ev in evidence_map.items() if ev["type"] == "document_text"]
            inc_eids = [eid for eid, ev in evidence_map.items() if "product_incidents" in str(ev["content"])]
            rec_eids = (pm_eids + inc_eids)[:2] or all_used_eids[:1]

            recommendations.append({
                "recommendation_id": "REC-001",
                "action": "Implement end-to-end webhook integration test suites for billing-gateway before future releases.",
                "rationale": "Prevent unhandled webhook response schema regressions from causing automated customer account lockouts.",
                "evidence_ids": rec_eids,
                "priority": PriorityLevel.CRITICAL.value,
            })
            recommendations.append({
                "recommendation_id": "REC-002",
                "action": "Initiate proactive customer success outreach and billing credit adjustments for impacted Pro/Enterprise accounts.",
                "rationale": "Remediate customer dissatisfaction and restore wrongfully cancelled enterprise accounts.",
                "evidence_ids": all_used_eids[:2],
                "priority": PriorityLevel.HIGH.value,
            })

            executive_summary = (
                "The investigation revealed that the September 2025 customer cancellation spike was directly "
                "caused by a webhook regression in billing-gateway release v2.4.0. The bug erroneously flagged valid payments "
                "as failed (causing a 10x surge in failure rates), triggered automated account lockouts, overloaded support queues, "
                "and resulted in elevated churn among Pro and Enterprise accounts."
            )
            limitations = [
                "Analysis is restricted to data available in relational telemetry and internal postmortems up to Q3 2025.",
                "Direct customer communication logs were reviewed via aggregated support ticket metrics."
            ]
        elif findings:
            # Findings exist but root cause not conclusively proven
            executive_summary = "Partial investigation findings were identified, but conclusive root cause could not be established."
            limitations = ["Available evidence does not fully isolate a single deterministic root cause."]
        else:
            # Generic fallback for unmapped evidence
            for i, (eid, ev) in enumerate(evidence_map.items(), 1):
                findings.append({
                    "finding_id": f"FND-{i:03d}",
                    "statement": f"Evidence recorded from {ev['tool']} (source: {ev['source_ref']}).",
                    "evidence_ids": [eid],
                    "confidence": ConfidenceLevel.MEDIUM.value,
                })
                all_used_eids.append(eid)
            executive_summary = f"Evidence from {len(evidence_map)} sources was reviewed."
            limitations = ["Generic evidence gathered without specific anomaly indicators."]

        unique_eids = list(dict.fromkeys(all_used_eids))
        report_data = {
            "investigation_run_id": run_id,
            "question": question,
            "executive_summary": executive_summary,
            "findings": findings,
            "root_cause": root_cause,
            "contributing_factors": contributing_factors,
            "recommendations": recommendations,
            "limitations": limitations,
            "evidence_ids": unique_eids,
            "citation_valid": False,  # will be verified by CitationValidator
            "synthesis_status": SynthesisStatus.SUCCESS.value if root_cause else (
                SynthesisStatus.SUCCESS.value if findings else SynthesisStatus.INSUFFICIENT_EVIDENCE.value
            ),
            "validation_errors": [],
            "metadata": {
                "provider": "MockLLMProvider",
                "evidence_items_reviewed": len(evidence_map),
            }
        }
        return json.dumps(report_data)
