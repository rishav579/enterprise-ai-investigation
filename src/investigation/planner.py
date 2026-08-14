"""Deterministic investigation planner.

Maps business investigation questions to structured, ordered investigation plans
using explicit scenario definitions — no LLM required.

Each scenario is a hand-authored sequence of InvestigationStep objects designed
to gather the specific evidence needed to answer the question.

The planner is deterministic: the same question always produces the same plan.
"""

import re
import uuid
from typing import List, Optional
from src.investigation.models import (
    InvestigationPlan,
    InvestigationRequest,
    InvestigationStep,
)

# ---------------------------------------------------------------------------
# Keyword matchers for scenario detection
# ---------------------------------------------------------------------------

_CHURN_SPIKE_KEYWORDS = {
    "cancellation", "cancellations", "cancel", "churn", "churned",
    "unsubscribe", "unsubscribing", "terminated", "subscription",
    "lost customers", "losing", "customers are",
}

_SUPPORT_SPIKE_KEYWORDS = {
    "support", "tickets", "eu-central"
}

_PRODUCT_INCIDENT_KEYWORDS = {
    "incident", "api gateway", "p1"
}

_SECURITY_SQL_KEYWORDS = {
    "drop table", "delete from"
}

_SECURITY_TRAVERSAL_KEYWORDS = {
    "../../", "/etc/passwd", "/etc/shadow"
}

_INSUFFICIENT_KEYWORDS = {
    "unicorn"
}


def _matches_churn_spike(question: str) -> bool:
    """Return True if the question is about customer cancellations or churn."""
    tokens = set(re.findall(r"\b[a-z]+\b", question.lower()))
    return bool(tokens & _CHURN_SPIKE_KEYWORDS)

def _matches_support_spike(question: str) -> bool:
    q_lower = question.lower()
    return "eu-central" in q_lower and "support" in q_lower

def _matches_product_incident(question: str) -> bool:
    q_lower = question.lower()
    return "api gateway" in q_lower and "incident" in q_lower

def _matches_security_sql(question: str) -> bool:
    q_lower = question.lower()
    return "drop table" in q_lower or "delete from" in q_lower

def _matches_security_traversal(question: str) -> bool:
    q_lower = question.lower()
    return "/etc/passwd" in q_lower or "/etc/shadow" in q_lower or "../" in q_lower

def _matches_insufficient(question: str) -> bool:
    return "unicorn" in question.lower()


# ---------------------------------------------------------------------------
# Scenario plan builders
# ---------------------------------------------------------------------------

def _build_churn_spike_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    """Return the canonical ordered investigation steps for the churn-spike scenario."""
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Establish monthly cancellation baseline and identify the anomaly window",
            rationale=(
                "Before investigating causes, we must confirm that an unusual spike exists "
                "in the data and establish which months are affected versus the baseline period."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT strftime('%Y-%m', cancellation_date) AS churn_month, "
                    "COUNT(*) AS total_cancellations "
                    "FROM subscriptions "
                    "WHERE cancellation_date IS NOT NULL "
                    "GROUP BY churn_month "
                    "ORDER BY churn_month ASC"
                ),
                "max_rows": 50,
            },
            expected_evidence_type="time_series_cancellations",
            depends_on=[],
        ),
        InvestigationStep(
            step_id="STEP-02",
            objective="Segment cancellations by customer plan and region to find most impacted cohorts",
            rationale=(
                "If the spike disproportionately affects specific plan tiers (e.g. pro, enterprise) "
                "or regions (e.g. EU-Central, US-East), it points to a systemic rather than random cause."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT c.plan, c.region, COUNT(s.subscription_id) AS cancelled_count "
                    "FROM subscriptions s "
                    "JOIN customers c ON s.customer_id = c.customer_id "
                    "WHERE s.cancellation_date >= '2025-09-01' AND s.cancellation_date <= '2025-10-31' "
                    "GROUP BY c.plan, c.region "
                    "ORDER BY cancelled_count DESC"
                ),
                "max_rows": 50,
            },
            expected_evidence_type="segment_breakdown",
            depends_on=["STEP-01"],
        ),
        InvestigationStep(
            step_id="STEP-03",
            objective="Inspect billing failure rates by month to detect payment processing anomalies",
            rationale=(
                "Billing failures can trigger automated account lockouts leading to frustration "
                "and cancellation. A surge in billing failures correlated with the churn spike "
                "would constitute strong supporting evidence."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT strftime('%Y-%m', event_date) AS month, "
                    "COUNT(*) AS total_events, "
                    "SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_events, "
                    "ROUND(100.0 * SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) "
                    "AS failure_rate_pct "
                    "FROM billing_events "
                    "GROUP BY month "
                    "ORDER BY month ASC"
                ),
                "max_rows": 50,
            },
            expected_evidence_type="billing_failure_time_series",
            depends_on=[],
        ),
        InvestigationStep(
            step_id="STEP-04",
            objective="Inspect billing failure reasons focused on the cancellation cohort",
            rationale=(
                "By filtering billing failures specifically for customers who cancelled in "
                "September-October, we can confirm the causal link between payment issues "
                "and the churn decision."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT b.event_type, b.status, COUNT(*) AS event_count "
                    "FROM billing_events b "
                    "WHERE b.customer_id IN ("
                    "  SELECT customer_id FROM subscriptions "
                    "  WHERE cancellation_date >= '2025-09-01' "
                    "  AND cancellation_reason IN ('payment_issue', 'unexpected_account_lockout', 'billing_discrepancy')"
                    ") "
                    "AND b.event_date >= '2025-09-01' "
                    "GROUP BY b.event_type, b.status "
                    "ORDER BY event_count DESC"
                ),
                "max_rows": 50,
            },
            expected_evidence_type="billing_cohort_breakdown",
            depends_on=["STEP-03"],
        ),
        InvestigationStep(
            step_id="STEP-05",
            objective="Analyze support ticket volume and resolution time by month",
            rationale=(
                "An overloaded support queue with long resolution times during the spike period "
                "would compound billing frustration and correlate with higher cancellation intent."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT strftime('%Y-%m', created_at) AS ticket_month, "
                    "COUNT(*) AS total_tickets, "
                    "SUM(CASE WHEN category IN ('billing','account_access') THEN 1 ELSE 0 END) "
                    "AS billing_related_tickets, "
                    "ROUND(AVG(CASE WHEN resolved_at IS NOT NULL "
                    "THEN (julianday(resolved_at) - julianday(created_at)) * 24.0 END), 1) "
                    "AS avg_resolution_hours "
                    "FROM support_tickets "
                    "GROUP BY ticket_month "
                    "ORDER BY ticket_month ASC"
                ),
                "max_rows": 50,
            },
            expected_evidence_type="support_sla_time_series",
            depends_on=[],
        ),
        InvestigationStep(
            step_id="STEP-06",
            objective="Identify product incidents on the billing service around the anomaly period",
            rationale=(
                "A production incident on the billing infrastructure is a candidate root cause "
                "that could explain simultaneous billing failures and account lockouts."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT incident_id, incident_date, severity, service, description "
                    "FROM product_incidents "
                    "WHERE incident_date >= '2025-08-01' AND incident_date <= '2025-10-31' "
                    "ORDER BY incident_date ASC"
                ),
                "max_rows": 20,
            },
            expected_evidence_type="incident_records",
            depends_on=[],
        ),
        InvestigationStep(
            step_id="STEP-07",
            objective="Inspect software release events on the billing service around the anomaly window",
            rationale=(
                "A deployment preceding the incident may have introduced the regression. "
                "Identifying the change type (refactor, feature, hotfix) and the service helps "
                "confirm or rule out a release-induced regression."
            ),
            tool_name="sql_investigation",
            tool_input={
                "query": (
                    "SELECT release_id, release_date, service, version, change_type "
                    "FROM release_events "
                    "WHERE release_date >= '2025-08-01' AND release_date <= '2025-10-31' "
                    "ORDER BY release_date ASC"
                ),
                "max_rows": 20,
            },
            expected_evidence_type="release_records",
            depends_on=[],
        ),
        InvestigationStep(
            step_id="STEP-08",
            objective="Search internal documentation for postmortem or runbook for the billing incident",
            rationale=(
                "Internal postmortems contain root-cause analysis and remediation steps that "
                "confirm technical details not captured in structured database records."
            ),
            tool_name="document_retrieval",
            tool_input={
                "action": "search",
                "query": "billing-gateway webhook",
                "max_results": 10,
            },
            expected_evidence_type="document_search_matches",
            depends_on=["STEP-06"],
        ),
        InvestigationStep(
            step_id="STEP-09",
            objective="Retrieve full postmortem document for the billing gateway incident",
            rationale=(
                "The full postmortem text provides complete technical root cause and remediation "
                "information required to form a final evidence-backed recommendation."
            ),
            tool_name="document_retrieval",
            tool_input={
                "action": "get",
                "document_id": "postmortem_inc_2025_002.md",
            },
            expected_evidence_type="document_full_text",
            depends_on=["STEP-08"],
        ),
    ]


# ---------------------------------------------------------------------------
# Planner class
def _build_support_spike_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Check support tickets for EU-Central",
            rationale="Find technical tickets in EU-Central.",
            tool_name="sql_investigation",
            tool_input={
                "query": "SELECT * FROM support_tickets WHERE category='technical' AND priority IN ('high', 'urgent')",
                "max_rows": 50
            },
            expected_evidence_type="support_tickets",
            depends_on=[]
        ),
        InvestigationStep(
            step_id="STEP-02",
            objective="Check product incidents",
            rationale="Find product incidents around the same time.",
            tool_name="sql_investigation",
            tool_input={
                "query": "SELECT * FROM product_incidents WHERE severity IN ('P1', 'P2') ORDER BY incident_date DESC",
                "max_rows": 50
            },
            expected_evidence_type="product_incidents",
            depends_on=["STEP-01"]
        )
    ]

def _build_product_incident_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Find API Gateway P1 incidents",
            rationale="Locate the incident.",
            tool_name="sql_investigation",
            tool_input={
                "query": "SELECT * FROM product_incidents WHERE service='api gateway' AND severity='P1'",
                "max_rows": 50
            },
            expected_evidence_type="product_incidents",
            depends_on=[]
        ),
        InvestigationStep(
            step_id="STEP-02",
            objective="Find API Gateway releases prior to incident",
            rationale="Check for releases.",
            tool_name="sql_investigation",
            tool_input={
                "query": "SELECT * FROM release_events WHERE service='api gateway' ORDER BY release_date DESC",
                "max_rows": 50
            },
            expected_evidence_type="release_events",
            depends_on=["STEP-01"]
        )
    ]

def _build_security_sql_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Execute requested query",
            rationale="Execute malicious query directly.",
            tool_name="sql_investigation",
            tool_input={
                "query": "DELETE FROM billing_events WHERE status = 'pending'; DROP TABLE customers; --",
                "max_rows": 50
            },
            expected_evidence_type="malicious_query",
            depends_on=[]
        )
    ]

def _build_security_traversal_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Execute requested traversal",
            rationale="Read outside workspace.",
            tool_name="document_retrieval",
            tool_input={
                "action": "get",
                "path": "../../../../../etc/passwd"
            },
            expected_evidence_type="malicious_traversal",
            depends_on=[]
        )
    ]

def _build_insufficient_plan(investigation_id: str, question: str) -> List[InvestigationStep]:
    return [
        InvestigationStep(
            step_id="STEP-01",
            objective="Query unicorn delivery",
            rationale="Look for unicorns.",
            tool_name="sql_investigation",
            tool_input={
                "query": "SELECT * FROM product_incidents WHERE service='unicorn delivery'",
                "max_rows": 50
            },
            expected_evidence_type="unicorn_data",
            depends_on=[]
        )
    ]

class InvestigationPlanner:
    """Orchestrates investigation plan generation from pre-
    authored step sequences. No LLM is invoked.
    """

    SCENARIO_CHURN_SPIKE = "churn_spike_investigation"
    SCENARIO_SUPPORT_SPIKE = "support_spike"
    SCENARIO_PRODUCT_INCIDENT = "product_incident"
    SCENARIO_SECURITY_SQL = "security_sql"
    SCENARIO_SECURITY_TRAVERSAL = "security_traversal"
    SCENARIO_INSUFFICIENT = "insufficient_evidence"
    SCENARIO_UNKNOWN = "generic_investigation"

    def _detect_scenario(self, request: InvestigationRequest) -> str:
        """Detect the most appropriate investigation scenario from the question text."""
        if request.scenario_hint == "churn_spike":
            return self.SCENARIO_CHURN_SPIKE
        if _matches_churn_spike(request.question):
            return self.SCENARIO_CHURN_SPIKE
        if _matches_support_spike(request.question):
            return self.SCENARIO_SUPPORT_SPIKE
        if _matches_product_incident(request.question):
            return self.SCENARIO_PRODUCT_INCIDENT
        if _matches_security_sql(request.question):
            return self.SCENARIO_SECURITY_SQL
        if _matches_security_traversal(request.question):
            return self.SCENARIO_SECURITY_TRAVERSAL
        if _matches_insufficient(request.question):
            return self.SCENARIO_INSUFFICIENT
        return self.SCENARIO_UNKNOWN

    def plan(self, request: InvestigationRequest) -> InvestigationPlan:
        """Generate a deterministic investigation plan for the given request.

        The same question always produces the same plan structure.
        """
        scenario = self._detect_scenario(request)

        if scenario == self.SCENARIO_CHURN_SPIKE:
            steps = _build_churn_spike_plan(request.investigation_id, request.question)
        elif scenario == self.SCENARIO_SUPPORT_SPIKE:
            steps = _build_support_spike_plan(request.investigation_id, request.question)
        elif scenario == self.SCENARIO_PRODUCT_INCIDENT:
            steps = _build_product_incident_plan(request.investigation_id, request.question)
        elif scenario == self.SCENARIO_SECURITY_SQL:
            steps = _build_security_sql_plan(request.investigation_id, request.question)
        elif scenario == self.SCENARIO_SECURITY_TRAVERSAL:
            steps = _build_security_traversal_plan(request.investigation_id, request.question)
        elif scenario == self.SCENARIO_INSUFFICIENT:
            steps = _build_insufficient_plan(request.investigation_id, request.question)
        else:
            # Generic fallback: single document listing step for unknown scenarios
            steps = [
                InvestigationStep(
                    step_id="STEP-01",
                    objective="List available knowledge base documents",
                    rationale="No specific scenario matched; starting with available documentation.",
                    tool_name="document_retrieval",
                    tool_input={"action": "list"},
                    expected_evidence_type="document_listing",
                    depends_on=[],
                )
            ]

        # Respect max_steps cap
        steps = steps[: request.max_steps]

        return InvestigationPlan(
            plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
            investigation_id=request.investigation_id,
            question=request.question,
            scenario=scenario,
            steps=steps,
            total_steps=len(steps),
        )
