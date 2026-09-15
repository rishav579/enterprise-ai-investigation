"""Unit tests for the deterministic NIFTY dip-buy engine.

All expectations are hand-calculable on the small synthetic series below.
No LLM, no I/O, no network.
"""

from datetime import date, timedelta

from src.nifty.data_loader import PriceRow
from src.nifty.engine import (
    calculate_metrics,
    detect_signals,
    run_experiment,
    simulate_trades,
)
from src.nifty.models import ExperimentIntent


def make_rows(closes: list[float], opens: list[float] | None = None, start: date = date(2020, 1, 6)) -> list[PriceRow]:
    """Monday-anchored II trading-day rows; opens default to same-day close (exact)."""
    rows: list[PriceRow] = []
    d = start
    for i, c in enumerate(closes):
        o = (opens[i] if opens is not None else c)
        rows.append(PriceRow(d, o, c))
        d += timedelta(days=1)
    return rows


def intent(**kw) -> ExperimentIntent:
    base = dict(
        test_period_start=date(2020, 1, 1),
        test_period_end=date(2020, 12, 31),
    )
    base.update(kw)
    return ExperimentIntent(**base)


def test_threshold_boundaries():
    # -2.9% -> no signal; ~-3.2% -> signal; ~-4.3% -> signal
    rows = make_rows([100.0, 97.1, 94.0, 90.0])
    assert detect_signals(rows, -0.03) == [2, 3]
    assert 1 not in detect_signals(rows, -0.03)
    # Exact -3.00% (100 -> 97) is a signal: boundary is inclusive (<=).
    exact = make_rows([100.0, 97.0])
    assert detect_signals(exact, -0.03) == [1]


def test_next_day_open_entry_no_lookahead():
    # Signal on idx1 (100 -> 95 = -5%). Entry must be open of idx2, never close of idx1.
    rows = make_rows(
        closes=[100.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0],
        opens=[100.0, 99.0, 94.0, 97.0, 98.0, 99.0, 100.0, 101.0],
    )
    trades, skipped = simulate_trades(rows, [1], holding_days=5, cost_frac=0.001)
    assert skipped == 0
    assert len(trades) == 1
    assert trades[0].entry_price == 94.0  # open[idx2], not close[idx1]=95
    assert trades[0].exit_price == 100.0  # close[idx6] = entry_idx(2)+5-1
    assert trades[0].gross_return == 100.0 / 94.0 - 1
    assert trades[0].net_return == trades[0].gross_return - 0.001


def test_holding_period_exit_indexing():
    rows = make_rows(closes=[100.0, 95.0] + [100.0 + i for i in range(30)])
    for h, expected_exit in [(5, 1 + 1 + 5 - 1), (10, 1 + 1 + 10 - 1), (20, 1 + 1 + 20 - 1)]:
        trades, _ = simulate_trades(rows, [1], holding_days=h, cost_frac=0.0)
        assert len(trades) == 1
        assert trades[0].exit_price == rows[expected_exit].close
        assert trades[0].holding_days == h


def test_cost_reduces_return():
    rows = make_rows(closes=[100.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0])
    free, _ = simulate_trades(rows, [1], holding_days=5, cost_frac=0.0)
    paid, _ = simulate_trades(rows, [1], holding_days=5, cost_frac=0.001)
    assert paid[0].net_return < free[0].net_return
    assert paid[0].net_return == paid[0].gross_return - 0.001


def test_no_overlap_consecutive_signals_yield_one_trade():
    # idx1 and idx2 both qualify; second must be ignored while 5-day position open.
    rows = make_rows(closes=[100.0, 96.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0])
    assert detect_signals(rows, -0.03)[:2] == [1, 2]
    trades, _ = simulate_trades(rows, [1, 2], holding_days=5, cost_frac=0.0)
    assert len(trades) == 1
    assert trades[0].signal_date == rows[1].trading_date.isoformat()


def test_empty_sample_produces_no_false_average():
    rows = make_rows(closes=[100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    res = run_experiment(rows, intent())
    assert res.signals_detected == 0
    for m in res.per_holding:
        assert m.trade_count == 0
        assert m.average_net_return is None
        assert m.median_net_return is None
        assert m.win_rate is None
    assert any("No qualifying signals" in w for w in res.warnings)


def test_insufficient_future_rows_skipped_with_warning():
    # Signal on last-1 index: entry exists but 5-day exit does not.
    rows = make_rows(closes=[100.0, 101.0, 102.0, 95.0, 96.0])
    assert detect_signals(rows, -0.03) == [3]
    res = run_experiment(rows, intent())
    assert res.signals_detected == 1
    assert res.per_holding[0].trade_count == 0
    assert any("past available data" in w or "No conclusion" in w for w in res.warnings)


def test_sensitivity_reports_all_holdings_primary_first():
    rows = make_rows(closes=[100.0, 95.0] + [96.0 + i for i in range(40)])
    res = run_experiment(rows, intent())
    assert [m.holding_days for m in res.per_holding] == [5, 10, 20]
    assert res.per_holding[0].is_primary is True
    assert all(m.is_primary is False for m in res.per_holding[1:])
    assert set(res.returns_by_holding.keys()) == {5, 10, 20}


def test_win_rate_and_median_math():
    rows = make_rows(closes=[100.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0])
    trades, _ = simulate_trades(rows, [1], holding_days=5, cost_frac=0.0)
    m = calculate_metrics(trades, 5, True)
    assert m.trade_count == 1
    assert m.average_net_return == trades[0].net_return
    assert m.median_net_return == trades[0].net_return
    assert m.win_rate == (1.0 if trades[0].net_return > 0 else 0.0)


def test_determinism():
    rows = make_rows(closes=[100.0, 95.0, 90.0, 93.0, 94.0, 95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0])
    exp = intent()
    first = run_experiment(rows, exp)
    second = run_experiment(rows, exp)
    assert first == second
