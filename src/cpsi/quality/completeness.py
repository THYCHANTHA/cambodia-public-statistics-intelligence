"""Per country x indicator completeness and plausibility warnings. Descriptive only: no value is altered."""

from __future__ import annotations

import pandas as pd

# Series where a negative value is meaningful (growth / inflation rates). Everywhere else negatives are flagged.
ALLOW_NEGATIVE = {"SP.POP.GROW", "NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG"}
# Units that are shares of a whole and so cannot exceed 100. Gross enrolment ratios and %-of-GDP are excluded
# on purpose (they can legitimately exceed 100).
BOUNDED_UNITS = {
    "% of total population",
    "% of population",
    "% of land area",
    "% of total employment",
    "% of total labor force",
    "% of people ages 15 and above",
    "% of total final energy consumption",
}
STALE_YEARS = 5


def completeness(obs: pd.DataFrame, countries: list[str], indicators: pd.DataFrame, start: int, end: int,
                 retrieved_at: str) -> pd.DataFrame:
    window = end - start + 1
    unit_of = indicators.set_index("indicator_code")["unit"].to_dict()
    valid = obs[obs["value"].notna()]
    grouped = {k: g for k, g in valid.groupby(["country_code", "indicator_code"])}
    rows = []
    for iso in countries:
        for code in indicators["indicator_code"]:
            g = grouped.get((iso, code))
            warnings = []
            if g is None or g.empty:
                n = 0
                first = latest = None
                gaps = 0
                span_pct = None
                warnings.append("no observations in window")
            else:
                n = len(g)
                first, latest = int(g["year"].min()), int(g["year"].max())
                span = latest - first + 1
                gaps = span - n
                span_pct = round(100 * n / span, 2)
                if gaps:
                    warnings.append(f"{gaps} missing year(s) between first and latest observation")
                if latest < end - STALE_YEARS:
                    warnings.append(f"latest observation is {latest} (older than {STALE_YEARS} years before {end})")
                if code not in ALLOW_NEGATIVE and (g["value"] < 0).any():
                    warnings.append("negative value(s) in a series that should be non-negative")
                if unit_of[code] in BOUNDED_UNITS and (g["value"] > 100).any():
                    warnings.append("value(s) above 100 in a share-of-whole series")
            rows.append(
                {
                    "country_code": iso,
                    "indicator_code": code,
                    "window_start": start,
                    "window_end": end,
                    "window_years": window,
                    "valid_observations": n,
                    "missing_observations": window - n,
                    "first_year": first,
                    "latest_year": latest,
                    "completeness_pct": round(100 * n / window, 2),
                    "span_completeness_pct": span_pct,
                    "internal_gap_years": gaps,
                    "validation_warnings": "; ".join(warnings) or None,
                    "retrieved_at": retrieved_at,
                }
            )
    return pd.DataFrame(rows)
