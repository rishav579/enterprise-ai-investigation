"""NIFTY experiment API boundary. Thin routes — all logic lives in src/nifty/.

Endpoints:
  POST /api/interpret   language -> proposed assumptions (no computation, no LLM in Phase 3)
  POST /api/experiment  validate + normalize an ExperimentIntent (no execution)
  POST /api/run         validate -> load data -> deterministic engine -> metrics (NO LLM)
  POST /api/explain     deterministic metrics -> three-section explanation (fallback, NO LLM)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.nifty.data_loader import DatasetError, load_price_data
from src.nifty.engine import ExperimentResult, run_experiment
from src.nifty.explain import (
    ExplainRequest,
    ExplainResponse,
    HoldingFact,
    build_fallback_explanation,
)
from src.nifty.interpret import InterpretRequest, InterpretResponse, interpret_question
from src.nifty.models import ExperimentIntent

router = APIRouter(prefix="/api", tags=["nifty"])

DATASET_NOTE = (
    "Synthetic mock NIFTY daily OHLC (seed 42). Not real market data. "
    "See data/nifty/DATA_NOTES.md."
)


class DatasetInfo(BaseModel):
    type: str = "synthetic_mock"
    source_note: str = DATASET_NOTE
    rows_in_period: int
    coverage_start: str
    coverage_end: str


class HoldingResult(BaseModel):
    holding_days: int
    is_primary: bool
    trade_count: int
    average_net_return: float | None
    median_net_return: float | None
    win_rate: float | None


class TradeResult(BaseModel):
    signal_date: str
    entry_date: str
    exit_date: str
    holding_days: int
    entry_price: float
    exit_price: float
    gross_return: float
    net_return: float


class RunResponse(BaseModel):
    experiment: ExperimentIntent
    dataset: DatasetInfo
    signals_detected: int
    primary: HoldingResult
    sensitivity: list[HoldingResult]
    warnings: list[str] = Field(default_factory=list)
    trades: list[TradeResult] = Field(default_factory=list)
    returns_by_holding: dict[int, list[float]] = Field(default_factory=dict)


def _to_run_response(intent: ExperimentIntent, result: ExperimentResult, n_rows: int, start: str, end: str) -> RunResponse:
    holdings = [
        HoldingResult(
            holding_days=m.holding_days,
            is_primary=m.is_primary,
            trade_count=m.trade_count,
            average_net_return=m.average_net_return,
            median_net_return=m.median_net_return,
            win_rate=m.win_rate,
        )
        for m in result.per_holding
    ]
    return RunResponse(
        experiment=intent,
        dataset=DatasetInfo(rows_in_period=n_rows, coverage_start=start, coverage_end=end),
        signals_detected=result.signals_detected,
        primary=holdings[0],
        sensitivity=holdings[1:],
        warnings=list(result.warnings),
        trades=[TradeResult(**t.__dict__) for t in result.trades_primary],
        returns_by_holding={h: list(v) for h, v in result.returns_by_holding.items()},
    )


@router.post("/interpret", response_model=InterpretResponse)
def interpret(payload: InterpretRequest) -> InterpretResponse:
    """Propose locked assumptions for a research question. Never computes results."""
    return interpret_question(payload.question.strip())


@router.post("/experiment", response_model=ExperimentIntent)
def validate_experiment(intent: ExperimentIntent) -> ExperimentIntent:
    """Validate user-confirmed assumptions. Returns the normalized experiment; does not run it."""
    return intent


@router.post("/run", response_model=RunResponse)
def run(intent: ExperimentIntent) -> RunResponse:
    """Run the deterministic experiment. No LLM is involved on this path."""
    try:
        rows = load_price_data(start=intent.test_period_start, end=intent.test_period_end)
    except DatasetError as exc:
        raise HTTPException(status_code=503, detail=f"Dataset unavailable: {exc}") from exc
    try:
        result = run_experiment(rows, intent)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # never leak internals; never fake a result
        raise HTTPException(status_code=500, detail=f"Experiment failed: {type(exc).__name__}") from exc
    return _to_run_response(intent, result, len(rows), rows[0].trading_date.isoformat(), rows[-1].trading_date.isoformat())


@router.post("/explain", response_model=ExplainResponse)
def explain(facts: ExplainRequest) -> ExplainResponse:
    """Explain supplied deterministic metrics. Uses only the given facts; computes nothing new."""
    primary = facts.primary
    if (primary.trade_count == 0) != (primary.average_net_return is None):
        raise HTTPException(
            status_code=422,
            detail="Inconsistent facts: zero trades must have null average_net_return and vice versa.",
        )
    return build_fallback_explanation(facts)


def explain_request_from_run(run: RunResponse) -> ExplainRequest:
    """Helper (also used by the smoke test): derive explain input strictly from a run response."""
    return ExplainRequest(
        threshold_pct=run.experiment.sharp_fall_threshold_pct,
        cost_bps=run.experiment.cost_bps,
        test_period_start=run.experiment.test_period_start.isoformat(),
        test_period_end=run.experiment.test_period_end.isoformat(),
        signals_detected=run.signals_detected,
        primary=HoldingFact(**run.primary.model_dump()),
        sensitivity=[HoldingFact(**s.model_dump()) for s in run.sensitivity],
        warnings=list(run.warnings),
    )
