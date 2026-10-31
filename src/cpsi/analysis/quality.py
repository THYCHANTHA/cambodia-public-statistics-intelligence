"""Reusable data-quality analysis on the long observation table. Input NaN values are never modified."""

from __future__ import annotations

import pandas as pd


def completeness_matrix(obs: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Percent of window years with a reported value; rows = countries, columns = indicators."""
    window = end - start + 1
    d = obs[(obs.year >= start) & (obs.year <= end) & obs.value.notna()]
    n = d.groupby(["country_code", "indicator_code"]).size().unstack("indicator_code")
    allc = sorted(obs.country_code.unique())
    alli = sorted(obs.indicator_code.unique())
    return (100 * n.reindex(index=allc, columns=alli).fillna(0) / window).round(1)


def missing_runs(s: pd.Series, start: int, end: int) -> pd.DataFrame:
    """Maximal runs of consecutive missing years in [start, end], typed as leading / internal / trailing / all."""
    full = s.reindex(range(start, end + 1))
    miss = full.isna().to_numpy()
    years = list(full.index)
    rep = [y for y, m in zip(years, miss, strict=True) if not m]
    runs, i = [], 0
    while i < len(years):
        if miss[i]:
            j = i
            while j + 1 < len(years) and miss[j + 1]:
                j += 1
            if not rep:
                kind = "all missing"
            elif years[j] < rep[0]:
                kind = "leading"
            elif years[i] > rep[-1]:
                kind = "trailing"
            else:
                kind = "internal"
            runs.append(
                {"first_missing_year": years[i], "last_missing_year": years[j], "length": j - i + 1, "type": kind}
            )
            i = j + 1
        else:
            i += 1
    return pd.DataFrame(runs, columns=["first_missing_year", "last_missing_year", "length", "type"])


def series_quality(s: pd.Series, start: int, end: int, stale_after_years: int = 5) -> dict:
    """Completeness, first/latest year, internal gap years, stale flag for one series."""
    v = s[(s.index >= start) & (s.index <= end)].dropna()
    window = end - start + 1
    if v.empty:
        return {"n_reported": 0, "completeness_pct": 0.0, "first_year": None, "latest_year": None,
                "internal_gap_years": 0, "stale": True, "stale_reason": "no reported observation"}
    first, latest = int(v.index.min()), int(v.index.max())
    stale = latest < end - stale_after_years
    return {
        "n_reported": len(v),
        "completeness_pct": round(100 * len(v) / window, 2),
        "first_year": first,
        "latest_year": latest,
        "internal_gap_years": (latest - first + 1) - len(v),
        "stale": stale,
        "stale_reason": f"latest {latest} is more than {stale_after_years} years before {end}" if stale else None,
    }


def historical_coverage(obs: pd.DataFrame, decades: range = range(1960, 2030, 10)) -> pd.DataFrame:
    """Per indicator and decade: percent of country-year cells reported (all countries present in ``obs``)."""
    ncountries = obs.country_code.nunique()
    rows = []
    for dec in decades:
        d = obs[(obs.year >= dec) & (obs.year < dec + 10)]
        for code, g in d.groupby("indicator_code"):
            cells = ncountries * g.year.nunique()
            pct = round(100 * g.value.notna().sum() / cells, 1)
            rows.append({"indicator_code": code, "decade": f"{dec}s", "coverage_pct": pct})
    return pd.DataFrame(rows)


def availability_by_country(obs: pd.DataFrame, end: int, recent_years: int = 5) -> pd.DataFrame:
    """Per country: indicators with any data, and indicators with a value in the last ``recent_years`` years."""
    total = obs.indicator_code.nunique()
    d = obs[obs.value.notna()]
    any_ = d.groupby("country_code").indicator_code.nunique()
    rec = d[d.year > end - recent_years].groupby("country_code").indicator_code.nunique()
    out = pd.DataFrame({"indicators_with_any_data": any_, "indicators_with_recent_data": rec}).reindex(
        sorted(obs.country_code.unique())).fillna(0).astype(int)
    out["indicators_total"] = total
    return out.rename_axis("country_code").reset_index()
