"""Exploratory Pearson / Spearman correlation on aligned country-year pairs. Correlation is not causation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

MIN_PAIRS = 8
CAVEAT = (
    "Exploratory only; correlation does not establish causality. p-values assume independent pairs, which "
    "country-year data are not (serial correlation within a country, shared trends), so treat them as indicative."
)


def aligned_pairs(obs: pd.DataFrame, x_code: str, y_code: str, countries: list[str] | None = None,
                  start: int | None = None, end: int | None = None) -> pd.DataFrame:
    """Country-years where BOTH indicators are reported (pairwise deletion; nothing is filled)."""
    d = obs if countries is None else obs[obs["country_code"].isin(countries)]
    if start is not None:
        d = d[d["year"] >= start]
    if end is not None:
        d = d[d["year"] <= end]
    x = d[d["indicator_code"] == x_code].set_index(["country_code", "year"])["value"].rename("x")
    y = d[d["indicator_code"] == y_code].set_index(["country_code", "year"])["value"].rename("y")
    return pd.concat([x, y], axis=1, join="inner").dropna().reset_index()


def correlate(pairs: pd.DataFrame, min_pairs: int = MIN_PAIRS) -> dict:
    n = len(pairs)
    res = {"n_pairs": n, "pearson_r": np.nan, "pearson_p": np.nan, "spearman_rho": np.nan, "spearman_p": np.nan,
           "status": "ok", "caveat": CAVEAT}
    if n < min_pairs:
        res["status"] = f"insufficient data: {n} pairs, at least {min_pairs} required"
        return res
    if pairs["x"].nunique() < 2 or pairs["y"].nunique() < 2:
        res["status"] = "undefined: one variable is constant"
        return res
    r, p = stats.pearsonr(pairs["x"], pairs["y"])
    rho, sp = stats.spearmanr(pairs["x"], pairs["y"])
    res.update(pearson_r=float(r), pearson_p=float(p), spearman_rho=float(rho), spearman_p=float(sp))
    return res


def correlate_by_country(pairs: pd.DataFrame, min_pairs: int = MIN_PAIRS) -> pd.DataFrame:
    rows = [{"country_code": c, **correlate(g, min_pairs)} for c, g in pairs.groupby("country_code")]
    return pd.DataFrame(rows).drop(columns="caveat") if rows else pd.DataFrame()
