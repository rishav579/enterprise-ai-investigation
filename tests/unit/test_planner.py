"""Unit tests for the deterministic InvestigationPlanner."""

import pytest
from src.investigation.models import InvestigationRequest, InvestigationStatus, StepStatus
from src.investigation.planner import InvestigationPlanner


@pytest.fixture
def planner():
    return InvestigationPlanner()


@pytest.fixture
def churn_request():
    return InvestigationRequest(
        question="Why did customer cancellations increase sharply in September 2025?",
        investigation_id="INV-TEST-001",
    )


def test_planner_produces_plan_for_churn_question(planner, churn_request):
    """Planner must produce a valid plan for the churn spike scenario."""
    plan = planner.plan(churn_request)

    assert plan.investigation_id == "INV-TEST-001"
    assert plan.question == churn_request.question
    assert plan.scenario == "churn_spike_investigation"
    assert len(plan.steps) > 0
    assert plan.total_steps == len(plan.steps)


def test_planner_is_deterministic(planner, churn_request):
    """Same question always produces the same step sequence (deterministic)."""
    plan_a = planner.plan(churn_request)
    plan_b = planner.plan(churn_request)

    assert len(plan_a.steps) == len(plan_b.steps)
    for step_a, step_b in zip(plan_a.steps, plan_b.steps):
        assert step_a.step_id == step_b.step_id
        assert step_a.tool_name == step_b.tool_name
        assert step_a.tool_input == step_b.tool_input
        assert step_a.depends_on == step_b.depends_on


def test_planner_churn_plan_covers_expected_dimensions(planner, churn_request):
    """Churn spike plan must include steps covering all required investigation dimensions."""
    plan = planner.plan(churn_request)

    tool_names = {s.tool_name for s in plan.steps}
    evidence_types = {s.expected_evidence_type for s in plan.steps}

    # Must use both available tools
    assert "sql_investigation" in tool_names
    assert "document_retrieval" in tool_names

    # Must cover cancellations, billing, support, incidents, releases, and documents
    assert "time_series_cancellations" in evidence_types
    assert "billing_failure_time_series" in evidence_types
    assert "support_sla_time_series" in evidence_types
    assert "incident_records" in evidence_types
    assert "release_records" in evidence_types
    assert "document_full_text" in evidence_types


def test_planner_churn_step_ids_are_unique_and_ordered(planner, churn_request):
    """Step IDs must be unique and follow a progressive order."""
    plan = planner.plan(churn_request)

    step_ids = [s.step_id for s in plan.steps]
    assert len(step_ids) == len(set(step_ids)), "Step IDs must be unique within the plan"
    assert step_ids == sorted(step_ids), "Step IDs must be in ascending order"


def test_planner_steps_have_valid_dependencies(planner, churn_request):
    """All step dependencies must reference step_ids that appear earlier in the plan."""
    plan = planner.plan(churn_request)

    seen_ids = set()
    for step in plan.steps:
        for dep in step.depends_on:
            assert dep in seen_ids, (
                f"Step {step.step_id} depends on '{dep}' which is not defined before it."
            )
        seen_ids.add(step.step_id)


def test_planner_keyword_variations_match_churn_scenario(planner):
    """Common keyword variations should all route to the churn spike scenario."""
    questions = [
        "Why did churn go up last quarter?",
        "What caused the cancellation rate to spike?",
        "Customers are unsubscribing at a higher rate, why?",
        "We are losing customers — investigate please.",
    ]
    for question in questions:
        plan = planner.plan(InvestigationRequest(question=question))
        assert plan.scenario == "churn_spike_investigation", (
            f"Expected churn_spike_investigation for question: {question}"
        )


def test_planner_unknown_question_returns_generic_plan(planner):
    """A question that doesn't match any scenario produces the generic fallback plan."""
    plan = planner.plan(InvestigationRequest(question="What is the meaning of life?"))
    assert plan.scenario == "generic_investigation"
    assert len(plan.steps) >= 1


def test_planner_respects_max_steps_cap(planner):
    """max_steps parameter must cap the number of steps returned."""
    plan = planner.plan(
        InvestigationRequest(
            question="Why did customer cancellations increase sharply in September 2025?",
            max_steps=3,
        )
    )
    assert len(plan.steps) <= 3
    assert plan.total_steps == len(plan.steps)


def test_planner_hint_overrides_detection(planner):
    """scenario_hint='churn_spike' must force churn scenario regardless of question text."""
    plan = planner.plan(
        InvestigationRequest(
            question="An ambiguous business question",
            scenario_hint="churn_spike",
        )
    )
    assert plan.scenario == "churn_spike_investigation"
