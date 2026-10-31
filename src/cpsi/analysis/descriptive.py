"""Descriptive statistics on reported (non-null) observations only."""

from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNS = [
    "country_code", "indicator_code", "window_start", "window_end", "window_years",
    "n_reported", "n_missing", "completeness_pct", "mean", "median", "min", "max", "std",
    "first_year", "latest_year", "latest_value",
]


def describe_series(s: pd.Series, start: int, end: int) -> dict:
    """``s`` is indexed by year; NaN means missing. Only years inside [start, end] are used."""
    s = s[(s.index >= start) & (s.index <= end)]
    v = s.dropna()
    n = len(v)
    window = end - start + 1
    return {
        "window_start": start,
        "window_end": end,
        "window_years": window,
        "n_reported": n,
        "n_missing": window - n,
        "completeness_pct": round(100 * n / window, 2),
        "mean": v.mean() if n else np.nan,
        "median": v.median() if n else np.nan,
        "min": v.min() if n else np.nan,
        "max": v.max() if n else np.nan,
        "std": v.std(ddof=1) if n > 1 else np.nan,  # sample standard deviation; undefined for n < 2
        "first_year": int(v.index.min()) if n else None,
        "latest_year": int(v.index.max()) if n else None,
        "latest_value": v.iloc[v.index.argmax()] if n else np.nan,
    }


def describe(obs: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """One row per country-indicator in ``obs`` (long table with country_code, indicator_code, year, value)."""
    rows = []
    for (c, i), g in obs.groupby(["country_code", "indicator_code"]):
        stats = describe_series(g.set_index("year")["value"], start, end)
        rows.append({"country_code": c, "indicator_code": i, **stats})
    return pd.DataFrame(rows, columns=COLUMNS)
