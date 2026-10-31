"""Outlier flags for review. Observations are never removed or changed; flags are a separate output."""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_OBS = 8
GROWTH_RATE_CODES = {"SP.POP.GROW", "NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG"}


def iqr_bounds(v: pd.Series, k: float = 1.5) -> tuple[float, float]:
    q1, q3 = v.quantile(0.25), v.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def robust_z(v: pd.Series) -> pd.Series:
    """0.6745 * (x - median) / MAD. NaN when MAD == 0 (more than half the values identical)."""
    med = v.median()
    mad = (v - med).abs().median()
    if mad == 0 or np.isnan(mad):
        return pd.Series(np.nan, index=v.index)
    return 0.6745 * (v - med) / mad


def flag_outliers(obs: pd.DataFrame, k: float = 1.5, z_threshold: float = 3.5, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """Per country-indicator series with >= min_obs reported values, return the flagged rows."""
    rows = []
    for _, g in obs.dropna(subset=["value"]).groupby(["country_code", "indicator_code"]):
        if len(g) < min_obs:
            continue
        lo, hi = iqr_bounds(g["value"], k)
        z = robust_z(g["value"])
        flagged = g.assign(iqr_lower=lo, iqr_upper=hi, robust_z=z.values)
        flagged["iqr_flag"] = (g["value"] < lo) | (g["value"] > hi)
        flagged["robust_z_flag"] = flagged["robust_z"].abs() > z_threshold
        rows.append(flagged[flagged["iqr_flag"] | flagged["robust_z_flag"]])
    cols = ["country_code", "indicator_code", "year", "value", "iqr_lower", "iqr_upper", "robust_z", "iqr_flag",
            "robust_z_flag"]
    return pd.concat(rows)[cols].reset_index(drop=True) if rows else pd.DataFrame(columns=cols)


def suspect_zeros(obs: pd.DataFrame, codes: set[str] = GROWTH_RATE_CODES) -> pd.DataFrame:
    """Exact 0.0 in a continuous growth-rate series is unusual and may be a placeholder. Flag for review only."""
    d = obs[obs["indicator_code"].isin(codes) & (obs["value"] == 0)]
    return d[["country_code", "indicator_code", "year", "value"]].assign(
        review_note="exact zero in a growth-rate series: verify against the primary source; value left unchanged"
    ).reset_index(drop=True)
