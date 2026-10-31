"""Year-to-year change and rolling means. Never bridges missing years, never interpolates.

Definitions (also in docs/methodology.md):
* absolute change_t      = value_t - value_{t-1}, only if year t-1 has a reported value.
* percentage growth_t    = (value_t / value_{t-1} - 1) * 100, only if year t-1 is reported AND value_{t-1} > 0.
  Offered for ``level`` and ``rate`` indicators; not for ``percent`` indicators (shares, growth rates).
* percentage-point change = value_t - value_{t-1} for ``percent`` indicators (a difference of two percentages).
* rolling mean (w)       = mean of w CONSECUTIVE calendar years ending at t, requiring all w years reported.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GROWTH_KINDS = {"level", "rate"}


def _full(s: pd.Series) -> pd.Series:
    """Reindex to every calendar year between first and last label so that gaps become explicit NaN."""
    s = s.sort_index()
    if s.empty:
        return s.astype(float)
    return s.reindex(range(int(s.index.min()), int(s.index.max()) + 1)).astype(float)


def annual_changes(s: pd.Series, kind: str) -> pd.DataFrame:
    """Return year, value, previous_value (the immediately preceding calendar year only) and the changes."""
    full = _full(s)
    prev = full.shift(1)  # positional shift on a gap-free index == previous calendar year
    ok = full.notna() & prev.notna()
    change = (full - prev).where(ok)
    out = pd.DataFrame({"year": full.index, "value": full.values, "previous_value": prev.values})
    out["absolute_change"] = change.values
    if kind == "percent":
        out["percentage_point_change"] = change.values
        out["percentage_growth"] = np.nan
    else:
        out["percentage_point_change"] = np.nan
        valid = ok & (prev > 0) if kind in GROWTH_KINDS else ok & False
        out["percentage_growth"] = ((full / prev - 1) * 100).where(valid).values
    return out.reset_index(drop=True)


def rolling_mean(s: pd.Series, window: int) -> pd.DataFrame:
    """Rolling mean over ``window`` consecutive calendar years; NaN unless all of them are reported."""
    if window < 2:
        raise ValueError("window must be >= 2")
    full = _full(s)
    out = pd.DataFrame({"year": full.index, "value": full.values})
    out["n_observations_in_window"] = full.notna().astype(int).rolling(window, min_periods=1).sum().values
    out["rolling_mean"] = full.rolling(window, min_periods=window).mean().values
    out["window"] = window
    return out.reset_index(drop=True)


def change_label(kind: str) -> str:
    return "percentage-point change" if kind == "percent" else "annual percentage growth"
