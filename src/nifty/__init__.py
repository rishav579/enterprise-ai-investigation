"""NIFTY dip-buy experiment package.

Separation principle (locked spec):
  LLM  -> language interpretation + explanation only (never arithmetic).
  Deterministic code here -> signals, trades, metrics, evidence.
"""

from src.nifty.models import DEFAULT_TEST_END, DEFAULT_TEST_START, ExperimentIntent

__all__ = ["ExperimentIntent", "DEFAULT_TEST_START", "DEFAULT_TEST_END"]
