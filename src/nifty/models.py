"""Typed experiment models. No arithmetic here — validation only."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# Default test period shown in UI and used when the user accepts defaults.
# Synthetic mock dataset covers this full range (see data/nifty/DATA_NOTES.md).
DEFAULT_TEST_START: date = date(2015, 1, 1)
DEFAULT_TEST_END: date = date(2024, 12, 31)

DEFAULT_THRESHOLD_PCT = -3.0
DEFAULT_COST_BPS = 10.0
PRIMARY_HOLDING_DAYS = 5
SENSITIVITY_HOLDING_DAYS: list[int] = [10, 20]


class ExperimentIntent(BaseModel):
    """Locked MVP experiment definition. All fields visible/editable in UI."""

    market: Literal["NIFTY50"] = "NIFTY50"
    sharp_fall_threshold_pct: float = Field(
        default=DEFAULT_THRESHOLD_PCT, description="Signal when daily close-to-close % <= threshold"
    )
    work_definition: Literal["avg_return"] = "avg_return"
    holding_days_primary: Literal[5] = 5
    holding_days_sensitivity: list[int] = Field(default_factory=lambda: [10, 20])
    entry_timing: Literal["next_open"] = "next_open"
    cost_bps: float = Field(default=DEFAULT_COST_BPS, description="Round-trip friction in basis points")
    allow_overlapping_positions: Literal[False] = False
    test_period_start: date = DEFAULT_TEST_START
    test_period_end: date = DEFAULT_TEST_END

    @field_validator("sharp_fall_threshold_pct")
    @classmethod
    def threshold_must_be_negative(cls, v: float) -> float:
        if v >= 0:
            raise ValueError("sharp_fall_threshold_pct must be negative (e.g. -3.0)")
        if v < -50:
            raise ValueError("threshold is unreasonably large (min -50%)")
        return v

    @field_validator("cost_bps")
    @classmethod
    def cost_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("cost_bps cannot be negative")
        if v > 200:
            raise ValueError("cost_bps is unreasonably large (max 200bps)")
        return v

    @field_validator("holding_days_sensitivity")
    @classmethod
    def sensitivity_must_be_positive(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("holding_days_sensitivity must not be empty")
        for h in v:
            if h <= 0 or h > 250:
                raise ValueError("each sensitivity holding period must be in 1..250")
        if 5 in v:
            raise ValueError("sensitivity list must not repeat the primary 5-day period")
        return v

    @model_validator(mode="after")
    def dates_must_be_ordered(self) -> "ExperimentIntent":
        if self.test_period_end <= self.test_period_start:
            raise ValueError("test_period_end must be after test_period_start")
        return self
