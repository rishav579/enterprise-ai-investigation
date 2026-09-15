# NIFTY Dataset — DATA_NOTES.md

## What this is
**Synthetic mock** daily OHLC reference series for the NIFTY dip-buy prototype
(`nifty_ohlc.csv`). It is NOT real NIFTY data and must never be presented as such.

## Why synthetic
The locked spec requires a deterministic local data layer with no live market-data
dependency. A seeded synthetic series keeps the demo reproducible offline while the
engine, API contracts, and UI are evaluated.

## Coverage
- 2015-01-01 .. 2024-12-31, Monday–Friday rows only (no exchange-holiday calendar —
  documented simplification; weekends excluded, holidays treated as trading days).
- 2609 rows. Columns used: `Date, Open, Close` (High/Low/Volume intentionally omitted;
  the engine only needs Open for entry and Close for signals/exits).

## Generation (seed 42)
- Start ≈ 8284. Daily overnight gap ~ N(+0.05%, 0.4%), intraday ~ N(+0.06%, 0.8%).
- 38 forced sharp-fall days (close-to-close −3.1% … −6%), including 4 in March 2020
  to mimic a stress cluster. Remaining falls are natural volatility tails.
- Result: 39 days with return ≤ −3%, terminal level ≈ 25173 (plausibly NIFTY-like;
  resemblance is coincidental).
- Generator: throwaway script (seed 42); CSV is the committed artifact.

## Known limitations
1. Synthetic — levels, drift, and crash dates do not match real NIFTY history.
2. No corporate actions, dividends, or total-return adjustment (price reference only).
3. No holiday calendar; no High/Low so no intraday stop-out modelling.
4. Treated as a theoretical index-price reference, not an ETF/futures/broker feed.
5. Swapping in real OHLC CSV with the same columns requires no engine change.

## Swapping in real data
Replace `data/nifty/nifty_ohlc.csv` with real NIFTY 50 daily data using identical
headers (`Date` ISO YYYY-MM-DD, `Open`, `Close`), keep it sorted, and update this
note with source, vendor, and coverage dates.
