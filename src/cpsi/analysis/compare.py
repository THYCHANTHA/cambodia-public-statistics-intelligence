"""Cross-country comparison for ONE indicator and ONE reference year. No aggregates are created."""

from __future__ import annotations

import numpy as np
import pandas as pd

BENCHMARK_NOTE = "External benchmark, not an ASEAN member."


def select_countries(countries: pd.DataFrame, group: str, custom: list[str] | None = None) -> list[str]:
    """group: 'asean' | 'khm_vs_cze' | 'custom' | 'all'."""
    if group == "asean":
        return countries.loc[countries.country_group == "ASEAN", "iso3"].tolist()
    if group == "khm_vs_cze":
        return ["KHM", "CZE"]
    if group == "custom":
        return list(custom or [])
    if group == "all":
        return countries["iso3"].tolist()
    raise ValueError(f"unknown comparison group: {group}")


def latest_common_year(obs: pd.DataFrame, indicator: str, countries: list[str]) -> int | None:
    """Most recent year in which EVERY selected country has a reported value (None if there is none)."""
    d = obs[(obs.indicator_code == indicator) & obs.country_code.isin(countries) & obs.value.notna()]
    if d.empty or d.country_code.nunique() < len(set(countries)):
        return None
    sets = [set(g.year) for _, g in d.groupby("country_code")]
    common = set.intersection(*sets)
    return max(common) if common else None


def compare_year(obs: pd.DataFrame, countries_meta: pd.DataFrame, indicator: str, countries: list[str], year: int,
                 higher_is: str = "higher value = rank 1") -> pd.DataFrame:
    """One row per selected country. Values are taken ONLY from ``year``; countries without a value stay in the
    table as missing (with their latest reported year for context) and are not ranked."""
    d = obs[(obs.indicator_code == indicator) & obs.country_code.isin(countries)]
    meta = countries_meta.set_index("iso3")
    rows = []
    for c in countries:
        g = d[d.country_code == c]
        at = g[(g.year == year) & g.value.notna()]
        rep = g[g.value.notna()]
        note = []
        if c in meta.index:
            m = meta.loc[c]
            if m.country_group == "EXTERNAL_BENCHMARK":
                note.append(BENCHMARK_NOTE)
            since = m.asean_member_since
            if pd.notna(since) and year < pd.Timestamp(since).year:
                note.append(f"Value refers to {year}, before ASEAN membership ({pd.Timestamp(since).date()}).")
        rows.append({
            "country_code": c,
            "country_name": meta.loc[c, "country_name"] if c in meta.index else c,
            "year": year,
            "value": at.value.iloc[0] if len(at) else np.nan,
            "unit": g.unit.iloc[0] if len(g) else None,
            "status": "reported" if len(at) else "missing in this year",
            "latest_reported_year": int(rep.year.max()) if len(rep) else None,
            "note": " ".join(note) or None,
        })
    out = pd.DataFrame(rows)
    out["rank"] = out["value"].rank(ascending=False, method="min")
    out["n_ranked"] = int(out["value"].notna().sum())
    out.attrs["rank_rule"] = (
        f"Rank among countries with a reported value in {year} only; {higher_is}. Not a quality judgement."
    )
    return out.sort_values(["rank", "country_code"], na_position="last").reset_index(drop=True)
