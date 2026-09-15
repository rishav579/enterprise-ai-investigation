"""Deterministic offline question interpretation. No arithmetic, no backtest.

Phase 3: no live LLM. This recognizes the MVP prototype question and returns the
locked assumptions as *proposed* clarification — never financial facts or results.
An LLM-backed variant (Phase 5) must produce this same typed shape.
"""

from pydantic import BaseModel, Field

from src.nifty.models import (
    DEFAULT_COST_BPS,
    DEFAULT_TEST_END,
    DEFAULT_TEST_START,
    DEFAULT_THRESHOLD_PCT,
    PRIMARY_HOLDING_DAYS,
    SENSITIVITY_HOLDING_DAYS,
)


class InterpretRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)


class Ambiguity(BaseModel):
    field: str
    label: str
    why_it_matters: str


class SuggestedAssumptions(BaseModel):
    sharp_fall_threshold_pct: float = DEFAULT_THRESHOLD_PCT
    work_definition: str = "avg_return"
    holding_days_primary: int = PRIMARY_HOLDING_DAYS
    holding_days_sensitivity: list[int] = Field(default_factory=lambda: list(SENSITIVITY_HOLDING_DAYS))
    entry_timing: str = "next_open"
    cost_bps: float = DEFAULT_COST_BPS
    allow_overlapping_positions: bool = False
    test_period_start: str = Field(default=DEFAULT_TEST_START.isoformat())
    test_period_end: str = Field(default=DEFAULT_TEST_END.isoformat())


class InterpretResponse(BaseModel):
    question: str
    market: str = "NIFTY50"
    recognized: bool
    note: str
    ambiguities: list[Ambiguity]
    suggested_assumptions: SuggestedAssumptions
    explanations: dict[str, str]


_AMBIGUITIES = [
    Ambiguity(
        field="sharp_fall_threshold_pct",
        label="What counts as a sharp fall?",
        why_it_matters="The threshold decides which days qualify as signals and how large the sample is.",
    ),
    Ambiguity(
        field="work_definition",
        label="What does 'work' mean?",
        why_it_matters="'Work' could mean average return, win rate, or beating a benchmark — the verdict depends on it.",
    ),
    Ambiguity(
        field="holding_days_primary",
        label="How long should the position be held?",
        why_it_matters="Results are specific to the holding period; it must be fixed before seeing results.",
    ),
    Ambiguity(
        field="test_period",
        label="What historical period should be tested?",
        why_it_matters="Different periods contain different market regimes and different numbers of sharp falls.",
    ),
]

_EXPLANATIONS = {
    "sharp_fall_threshold_pct": (
        "Suggested assumption: a single-day NIFTY decline of 3% or more qualifies as a sharp fall. "
        "Why: it provides a simple, observable and reproducible starting definition."
    ),
    "work_definition": (
        "Suggested assumption: 'work' means a positive average net return over the primary holding period. "
        "Why: it is the simplest pre-committed success criterion; other readings (win rate, benchmarks) are future work."
    ),
    "holding_days_primary": (
        "Suggested assumption: hold 5 trading days as the primary outcome, with 10 and 20 days as sensitivity analysis only. "
        "Why: pre-committing prevents picking the best-looking horizon after seeing results."
    ),
    "entry_timing": (
        "Suggested assumption: enter at the next trading day's open. "
        "Why: the signal is only known after the trigger day's close, so same-day entry would be look-ahead."
    ),
    "cost_bps": (
        "Suggested assumption: 10 basis points (0.10%) round-trip friction. "
        "Why: a simplified prototype cost so results are net of friction; it is not any broker's actual fee."
    ),
    "allow_overlapping_positions": (
        "Suggested assumption: no overlapping positions — a new signal while a position is open is ignored. "
        "Why: keeps trades independent and the counting deterministic."
    ),
    "test_period": (
        "Suggested assumption: test over the full configured mock-data range. "
        "Why: multi-year coverage includes several market regimes; the range stays visible and editable."
    ),
}


def interpret_question(question: str) -> InterpretResponse:
    """Map a natural-language question to proposed locked assumptions (no computation)."""
    q = question.lower()
    recognized = "nifty" in q and any(w in q for w in ("fall", "dip", "declin", "drop", "crash", "sell-off", "selloff"))
    note = (
        "Recognized as the NIFTY dip-buy prototype question; assumptions below are the locked MVP defaults."
        if recognized
        else "Only the NIFTY dip-buy experiment is supported in this prototype; showing the locked MVP assumptions."
    )
    return InterpretResponse(
        question=question,
        recognized=recognized,
        note=note,
        ambiguities=list(_AMBIGUITIES),
        suggested_assumptions=SuggestedAssumptions(),
        explanations=dict(_EXPLANATIONS),
    )
