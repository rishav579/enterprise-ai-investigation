"""Deterministic CSV data layer. No network, no live API."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class PriceRow:
    trading_date: date
    open: float
    close: float


DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nifty" / "nifty_ohlc.csv"


class DatasetError(ValueError):
    pass


def load_price_data(
    csv_path: Path | str = DATASET_PATH,
    start: date | None = None,
    end: date | None = None,
) -> list[PriceRow]:
    """Load Date,Open,Close rows, sorted by date, optionally filtered to [start, end].

    Raises DatasetError on missing file, bad columns, bad values, or empty result.
    """
    path = Path(csv_path)
    if not path.exists():
        raise DatasetError(f"NIFTY dataset not found at {path}")
    rows: list[PriceRow] = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            if not {"Date", "Open", "Close"}.issubset(cols):
                raise DatasetError(f"Dataset must contain Date,Open,Close columns, got {reader.fieldnames}")
            for i, r in enumerate(reader, start=2):
                try:
                    d = date.fromisoformat(r["Date"].strip())
                    o = float(r["Open"])
                    c = float(r["Close"])
                except Exception as exc:
                    raise DatasetError(f"Invalid values on row {i}: {exc}") from exc
                if o <= 0 or c <= 0:
                    raise DatasetError(f"Non-positive price on row {i}")
                rows.append(PriceRow(d, o, c))
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError(f"Failed to read dataset: {exc}") from exc

    if not rows:
        raise DatasetError("Dataset is empty")
    rows.sort(key=lambda r: r.trading_date)
    # Fail clearly on duplicate dates rather than silently corrupting indexing.
    for a, b in zip(rows, rows[1:]):
        if a.trading_date == b.trading_date:
            raise DatasetError(f"Duplicate date in dataset: {a.trading_date}")

    if start is not None:
        rows = [r for r in rows if r.trading_date >= start]
    if end is not None:
        rows = [r for r in rows if r.trading_date <= end]
    if not rows:
        raise DatasetError("No rows in selected test period")
    return rows
