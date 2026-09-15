"""Deterministic fallback explanation. Uses ONLY supplied computed facts.

Phase 3: no live LLM. This formats /api/run output into the three LEARN sections
without inventing numbers, predictions, or advice. An LLM-backed variant (Phase 6)
must receive the same facts and obey the same wording guardrails.
"""

from pydantic import BaseModel, Field


class HoldingFact(BaseModel):
    holding_days: int
    is_primary: bool = False
    trade_count: int
    average_net_return: float | None = None
    median_net_return: float | None = None
    win_rate: float | None = None


class ExplainRequest(BaseModel):
    """The deterministic facts /api/run produced. No raw prices — metrics only."""

    threshold_pct: float = Field(..., description="Sharp-fall threshold, e.g. -3.0")
    cost_bps: float
    test_period_start: str
    test_period_end: str
    signals_detected: int
    primary: HoldingFact
    sensitivity: list[HoldingFact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExplainResponse(BaseModel):
    what_data_shows: str
    what_we_conclude: str
    what_to_investigate_next: list[str]


def _pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def build_fallback_explanation(facts: ExplainRequest) -> ExplainResponse:
    """Pure function: computed facts -> three cautious, advice-free sections."""
    p = facts.primary

    if p.trade_count == 0 or p.average_net_return is None:
        shows = (
            f"{facts.signals_detected} qualifying signal(s) were detected for a single-day fall "
            f"of {facts.threshold_pct}% or worse "
            f"({facts.test_period_start} to {facts.test_period_end}), "
            f"but no complete {p.holding_days}-day trade could be formed after costs of {facts.cost_bps} bps. "
            "No conclusion can be drawn."
        )
        conclude = (
            "With no measurable sample under these assumptions, there is nothing to conclude. "
            "This is a historical observation about mock data, not evidence about future performance."
        )
    else:
        assert p.median_net_return is not None and p.win_rate is not None
        direction = "positive" if p.average_net_return > 0 else "negative" if p.average_net_return < 0 else "flat"
        shows = (
            f"{facts.signals_detected} qualifying signal(s) were detected "
            f"({facts.test_period_start} to {facts.test_period_end}); "
            f"{p.trade_count} completed {p.holding_days}-day trade(s) after applying "
            f"{facts.cost_bps} bps round-trip cost. "
            f"The average {p.holding_days}-day net return was {_pct(p.average_net_return)} ({direction}), "
            f"the median was {_pct(p.median_net_return)}, "
            f"and {p.win_rate * 100:.1f}% of trades ended positive."
        )
        for s in facts.sensitivity:
            if s.trade_count and s.average_net_return is not None:
                shows += (
                    f" Sensitivity ({s.holding_days}-day, n={s.trade_count}): "
                    f"average {_pct(s.average_net_return)}."
                )
        conclude = (
            f"Under this definition (≤{facts.threshold_pct}% single-day fall, "
            f"{p.holding_days}-day hold, {facts.cost_bps} bps cost) and this historical period, "
            f"the setup showed a {direction} historical tendency. "
            "This does not establish that the same effect will occur in future markets."
        )
    if any("Low sample size" in w for w in facts.warnings):
        conclude += " The sample is small, so interpret with extra caution."

    next_steps = [
        "What happens if the sharp-fall threshold changes (e.g. −2% or −5%)?",
        "Does the result persist in different market regimes or sub-periods?",
        "Would a matched random-entry benchmark change the conclusion?",
    ]
    return ExplainResponse(
        what_data_shows=shows,
        what_we_conclude=conclude,
        what_to_investigate_next=next_steps,
    )
