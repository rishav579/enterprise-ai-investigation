"""API tests for the NIFTY research prototype (Phase 3).

Sync TestClient against the real FastAPI app. No LLM, no network.
"""

from fastapi.testclient import TestClient

from src.api.main import app
from src.nifty.models import DEFAULT_TEST_END, DEFAULT_TEST_START

client = TestClient(app)

QUESTION = "Does buying NIFTY after a sharp fall work?"

VALID_EXPERIMENT = {
    "market": "NIFTY50",
    "sharp_fall_threshold_pct": -3.0,
    "work_definition": "avg_return",
    "holding_days_primary": 5,
    "holding_days_sensitivity": [10, 20],
    "entry_timing": "next_open",
    "cost_bps": 10.0,
    "allow_overlapping_positions": False,
    "test_period_start": DEFAULT_TEST_START.isoformat(),
    "test_period_end": DEFAULT_TEST_END.isoformat(),
}

BANNED_PHRASES = ["This strategy works", "You should buy", "will rebound", "NIFTY always"]


# ---------- /api/interpret ----------


def test_interpret_prototype_question_returns_locked_assumptions():
    r = client.post("/api/interpret", json={"question": QUESTION})
    assert r.status_code == 200
    body = r.json()
    assert body["market"] == "NIFTY50"
    assert body["recognized"] is True
    fields = {a["field"] for a in body["ambiguities"]}
    assert {"sharp_fall_threshold_pct", "work_definition", "holding_days_primary", "test_period"} <= fields
    sa = body["suggested_assumptions"]
    assert sa["sharp_fall_threshold_pct"] == -3.0
    assert sa["holding_days_primary"] == 5
    assert sa["holding_days_sensitivity"] == [10, 20]
    assert sa["entry_timing"] == "next_open"
    assert sa["cost_bps"] == 10.0
    assert sa["allow_overlapping_positions"] is False
    assert body["explanations"]["sharp_fall_threshold_pct"]


def test_interpret_does_not_execute_backtest():
    body = client.post("/api/interpret", json={"question": QUESTION}).json()
    raw = str(body)
    for key in ("average_net_return", "win_rate", "trade_count", "signals_detected"):
        assert key not in raw


def test_interpret_unrecognized_question_still_safe():
    r = client.post("/api/interpret", json={"question": "What about gold prices next week?"})
    assert r.status_code == 200
    body = r.json()
    assert body["recognized"] is False
    assert body["suggested_assumptions"]["sharp_fall_threshold_pct"] == -3.0


def test_interpret_rejects_too_short_question():
    assert client.post("/api/interpret", json={"question": "hi"}).status_code == 422


# ---------- /api/experiment ----------


def test_experiment_accepts_valid():
    r = client.post("/api/experiment", json=VALID_EXPERIMENT)
    assert r.status_code == 200
    assert r.json()["sharp_fall_threshold_pct"] == -3.0


def test_experiment_rejects_positive_threshold():
    bad = dict(VALID_EXPERIMENT, sharp_fall_threshold_pct=3.0)
    assert client.post("/api/experiment", json=bad).status_code == 422


def test_experiment_rejects_bad_dates():
    bad = dict(VALID_EXPERIMENT, test_period_start="2024-01-01", test_period_end="2015-01-01")
    r = client.post("/api/experiment", json=bad)
    assert r.status_code == 422


def test_experiment_rejects_sensitivity_repeating_primary():
    bad = dict(VALID_EXPERIMENT, holding_days_sensitivity=[5, 10])
    assert client.post("/api/experiment", json=bad).status_code == 422


def test_experiment_rejects_negative_cost():
    bad = dict(VALID_EXPERIMENT, cost_bps=-1.0)
    assert client.post("/api/experiment", json=bad).status_code == 422


# ---------- /api/run ----------


def test_run_returns_deterministic_metrics():
    r = client.post("/api/run", json=VALID_EXPERIMENT)
    assert r.status_code == 200
    body = r.json()
    assert body["experiment"]["sharp_fall_threshold_pct"] == -3.0
    assert body["dataset"]["type"] == "synthetic_mock"
    assert "Not real market data" in body["dataset"]["source_note"]
    assert body["signals_detected"] > 0
    assert body["primary"]["holding_days"] == 5
    assert body["primary"]["is_primary"] is True
    assert body["primary"]["trade_count"] > 0
    assert body["primary"]["average_net_return"] is not None
    assert [s["holding_days"] for s in body["sensitivity"]] == [10, 20]
    assert all(s["is_primary"] is False for s in body["sensitivity"])
    assert isinstance(body["warnings"], list)
    assert len(body["trades"]) == body["primary"]["trade_count"]
    # Trade-level evidence: entry is the day after the signal (no look-ahead).
    first = body["trades"][0]
    assert first["entry_date"] > first["signal_date"]
    assert first["exit_date"] >= first["entry_date"]


def test_run_is_deterministic():
    first = client.post("/api/run", json=VALID_EXPERIMENT).json()
    second = client.post("/api/run", json=VALID_EXPERIMENT).json()
    assert first == second


def test_run_rejects_invalid_experiment():
    bad = dict(VALID_EXPERIMENT, sharp_fall_threshold_pct=3.0)
    assert client.post("/api/run", json=bad).status_code == 422


def test_run_empty_sample_reports_no_false_average():
    impossible = dict(VALID_EXPERIMENT, sharp_fall_threshold_pct=-50.0)
    r = client.post("/api/run", json=impossible)
    assert r.status_code == 200
    body = r.json()
    assert body["signals_detected"] == 0
    assert body["primary"]["trade_count"] == 0
    assert body["primary"]["average_net_return"] is None
    assert any("No qualifying signals" in w for w in body["warnings"])


# ---------- /api/explain ----------


def _explain_input_from_run(run_body: dict) -> dict:
    return {
        "threshold_pct": run_body["experiment"]["sharp_fall_threshold_pct"],
        "cost_bps": run_body["experiment"]["cost_bps"],
        "test_period_start": run_body["experiment"]["test_period_start"],
        "test_period_end": run_body["experiment"]["test_period_end"],
        "signals_detected": run_body["signals_detected"],
        "primary": run_body["primary"],
        "sensitivity": run_body["sensitivity"],
        "warnings": run_body["warnings"],
    }


def test_explain_returns_three_sections_grounded_in_metrics():
    run_body = client.post("/api/run", json=VALID_EXPERIMENT).json()
    r = client.post("/api/explain", json=_explain_input_from_run(run_body))
    assert r.status_code == 200
    body = r.json()
    assert body["what_data_shows"]
    assert body["what_we_conclude"]
    assert len(body["what_to_investigate_next"]) >= 3
    # Grounded: cites the actual trade count and formatted average from the run.
    assert str(run_body["primary"]["trade_count"]) in body["what_data_shows"]
    assert f"{run_body['primary']['average_net_return'] * 100:+.2f}%" in body["what_data_shows"]
    for banned in BANNED_PHRASES:
        assert banned not in body["what_we_conclude"]
        assert banned not in body["what_data_shows"]


def test_explain_empty_sample_draws_no_conclusion():
    facts = _explain_input_from_run(
        client.post("/api/run", json=dict(VALID_EXPERIMENT, sharp_fall_threshold_pct=-50.0)).json()
    )
    body = client.post("/api/explain", json=facts).json()
    assert "No conclusion can be drawn" in body["what_data_shows"]
    for banned in BANNED_PHRASES:
        assert banned not in body["what_we_conclude"]


def test_explain_rejects_inconsistent_facts():
    facts = _explain_input_from_run(client.post("/api/run", json=VALID_EXPERIMENT).json())
    facts["primary"]["trade_count"] = 0  # contradicts non-null average
    assert client.post("/api/explain", json=facts).status_code == 422
