"""Deterministic dip-buy experiment engine. Pure functions, no I/O, no LLM.

Locked rules:
  daily_return = close[i] / close[i-1] - 1 ; signal when <= threshold
  entry = open of next trading day (never same-day close — no look-ahead)
  exit  = close of (entry_index + holding_days - 1)
  no overlapping positions: a signal on/before the active position's exit day is ignored
  net_return = gross_return - cost_frac  (cost_frac = cost_bps / 10000)
  insufficient future rows -> trade skipped, counted in warnings (documented rule)
"""

import statistics
from dataclasses import dataclass

from src.nifty.data_loader import PriceRow
from src.nifty.models import ExperimentIntent

LOW_SAMPLE_N = 10


@dataclass(frozen=True)
class Trade:
    signal_date: str
    entry_date: str
    exit_date: str
    holding_days: int
    entry_price: float
    exit_price: float
    gross_return: float
    net_return: float


@dataclass(frozen=True)
class HoldingMetrics:
    holding_days: int
    is_primary: bool
    trade_count: int
    average_net_return: float | None
    median_net_return: float | None
    win_rate: float | None


@dataclass(frozen=True)
class ExperimentResult:
    signals_detected: int
    warnings: list[str]
    per_holding: list[HoldingMetrics]
    trades_primary: list[Trade]
    # Net returns for every holding period (drives the single UI histogram).
    returns_by_holding: dict[int, list[float]]


def daily_returns(closes: list[float]) -> list[float | None]:
    """Close-to-close returns; index 0 is None (no previous close)."""
    out: list[float | None] = [None]
    for prev, cur in zip(closes, closes[1:]):
        out.append(cur / prev - 1)
    return out


def detect_signals(rows: list[PriceRow], threshold_frac: float) -> list[int]:
    """Return row indices i>=1 where close[i]/close[i-1]-1 <= threshold_frac."""
    signals: list[int] = []
    for i in range(1, len(rows)):
        if rows[i].close / rows[i - 1].close - 1 <= threshold_frac:
            signals.append(i)
    return signals


def simulate_trades(
    rows: list[PriceRow],
    signal_indices: list[int],
    holding_days: int,
    cost_frac: float,
) -> tuple[list[Trade], int]:
    """Walk signals in order; skip signals inside an open position or lacking future rows.

    Returns (trades, skipped_insufficient_rows).
    """
    trades: list[Trade] = []
    skipped = 0
    busy_until = -1  # exit index of active position; signals with idx <= this are ignored
    n = len(rows)
    for s in signal_indices:
        if s <= busy_until:
            continue
        entry_idx = s + 1
        exit_idx = entry_idx + holding_days - 1
        if entry_idx >= n or exit_idx >= n:
            skipped += 1
            continue
        entry_price = rows[entry_idx].open
        exit_price = rows[exit_idx].close
        gross = exit_price / entry_price - 1
        trades.append(
            Trade(
                signal_date=rows[s].trading_date.isoformat(),
                entry_date=rows[entry_idx].trading_date.isoformat(),
                exit_date=rows[exit_idx].trading_date.isoformat(),
                holding_days=holding_days,
                entry_price=entry_price,
                exit_price=exit_price,
                gross_return=gross,
                net_return=gross - cost_frac,
            )
        )
        busy_until = exit_idx
    return trades, skipped


def calculate_metrics(trades: list[Trade], holding_days: int, is_primary: bool) -> HoldingMetrics:
    if not trades:
        return HoldingMetrics(holding_days, is_primary, 0, None, None, None)
    nets = [t.net_return for t in trades]
    return HoldingMetrics(
        holding_days=holding_days,
        is_primary=is_primary,
        trade_count=len(trades),
        average_net_return=sum(nets) / len(nets),
        median_net_return=statistics.median(nets),
        win_rate=sum(1 for r in nets if r > 0) / len(nets),
    )


def run_experiment(rows: list[PriceRow], intent: ExperimentIntent) -> ExperimentResult:
    """Full deterministic run: primary 5-day + each sensitivity holding period."""
    if intent.allow_overlapping_positions:
        raise ValueError("MVP locks allow_overlapping_positions=False")
    threshold_frac = intent.sharp_fall_threshold_pct / 100.0
    cost_frac = intent.cost_bps / 10000.0
    signals = detect_signals(rows, threshold_frac)
    holdings = [intent.holding_days_primary, *intent.holding_days_sensitivity]

    warnings: list[str] = []
    per_holding: list[HoldingMetrics] = []
    returns_by_holding: dict[int, list[float]] = {}
    trades_primary: list[Trade] = []
    total_skipped = 0

    for h in holdings:
        trades, skipped = simulate_trades(rows, signals, h, cost_frac)
        total_skipped += 0 if h != intent.holding_days_primary else skipped
        per_holding.append(calculate_metrics(trades, h, h == intent.holding_days_primary))
        returns_by_holding[h] = [t.net_return for t in trades]
        if h == intent.holding_days_primary:
            trades_primary = trades

    if not signals:
        warnings.append("No qualifying signals were found for the selected parameters. No conclusion can be drawn.")
    else:
        primary_n = per_holding[0].trade_count
        if primary_n == 0:
            warnings.append(
                "Signals were detected but none could form a complete trade "
                "(insufficient future rows / overlap). No conclusion can be drawn."
            )
        elif primary_n < LOW_SAMPLE_N:
            warnings.append(f"Low sample size (n={primary_n}) — interpret with caution.")
        if total_skipped:
            warnings.append(
                f"{total_skipped} signal(s) near the end of the dataset were skipped "
                "(holding period extends past available data)."
            )
    return ExperimentResult(
        signals_detected=len(signals),
        warnings=warnings,
        per_holding=per_holding,
        trades_primary=trades_primary,
        returns_by_holding=returns_by_holding,
    )
