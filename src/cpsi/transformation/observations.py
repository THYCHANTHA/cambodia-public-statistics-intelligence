"""Turn cached World Bank bundles into standardized, validated long-format tables.

Missing values stay missing (NULL). Nothing is interpolated, filled or dropped. A value of 0 is kept as 0.
"""

from __future__ import annotations

import math

import pandas as pd

SOURCE_NAME = "World Development Indicators"
SOURCE_ORG_LABEL = "World Bank"
INDICATOR_URL = "https://data.worldbank.org/indicator/{code}"
LICENCE_DEFAULT = (
    "CC BY 4.0 (World Bank Open Data default). Third-party exceptions are possible: see source_organization."
)
LICENCE_CO2 = (
    "CC BY 4.0 as displayed on the World Bank indicator page (reported by the project owner on 2026-10-31; "
    "not independently re-read by the pipeline). Underlying data: EDGAR (JRC) and IEA."
)


class ValidationError(Exception):
    pass


def build_countries(records: list[dict], cfg: list[dict], retrieved_at: str) -> pd.DataFrame:
    by_id = {r["id"]: r for r in records}
    rows, missing = [], []
    for c in cfg:
        r = by_id.get(c["iso3"])
        if r is None:
            missing.append(c["iso3"])
            continue
        rows.append(
            {
                "iso3": c["iso3"],
                "country_name": r["name"],
                "iso2": r["iso2Code"],
                "world_bank_code": r["id"],
                "region": r["region"]["value"],
                "income_level": r["incomeLevel"]["value"],
                "capital_city": r["capitalCity"],
                "country_group": c["group"],
                "asean_member_since": c.get("asean_member_since"),
                "source": "World Bank country API",
                "retrieved_at": retrieved_at,
            }
        )
    if missing:
        raise ValidationError(f"countries missing from API response: {missing}")
    return pd.DataFrame(rows)


def build_indicators(
    meta: dict[str, tuple[dict, str]], cfg: list[dict], units: dict[str, dict]
) -> pd.DataFrame:
    """meta maps code -> (API metadata record, retrieved_at)."""
    rows = []
    for item in cfg:
        code = item["code"]
        rec, retrieved_at = meta[code]
        if rec["id"] != code:
            raise ValidationError(f"metadata id {rec['id']} != requested {code}")
        if code not in units:
            raise ValidationError(f"no unit entry for {code} in configs/units.yaml")
        u = units[code]
        notes = []
        if u.get("estimate_type"):
            notes.append(f"Indicator name states: {u['estimate_type']}.")
        if item.get("replaces"):
            notes.append(
                f"Replaces archived indicator {item['replaces']}. Different definition (excludes LULUCF, "
                "EDGAR/AR5 basis); the two must not be joined into one continuous series."
            )
        if u["basis"] == "inferred":
            notes.append("Unit inferred from name and definition: the API publishes no unit string.")
        rows.append(
            {
                "indicator_code": code,
                "indicator_name": rec["name"],
                "domain": item["domain"],
                "unit": u["unit"],
                "unit_basis": u["basis"],
                "value_kind": u["kind"],
                "estimate_type": u.get("estimate_type"),
                "replaces_code": item.get("replaces"),
                "definition": (rec.get("sourceNote") or "").strip(),
                "source_name": (rec.get("source") or {}).get("value", SOURCE_NAME),
                "source_url": INDICATOR_URL.format(code=code),
                "source_organization": (rec.get("sourceOrganization") or "").strip(),
                "frequency": "annual",
                "notes": " ".join(notes) or None,
                "licence": LICENCE_CO2 if item.get("replaces") else LICENCE_DEFAULT,
                "retrieved_at": retrieved_at,
            }
        )
    return pd.DataFrame(rows)


def parse_observations(
    records: list[dict],
    code: str,
    valid_iso3: set[str],
    unit: str,
    retrieved_at: str,
    start: int,
    end: int,
) -> tuple[pd.DataFrame, dict]:
    """Validate and standardize one indicator's records. Returns (frame, issues)."""
    issues = {"unknown_country": [], "indicator_mismatch": 0, "bad_year": [], "non_numeric": [],
              "out_of_window": [], "duplicates": []}
    rows, seen = [], set()
    for r in records:
        iso3 = r.get("countryiso3code")
        if iso3 not in valid_iso3:
            issues["unknown_country"].append(iso3)
            continue
        if (r.get("indicator") or {}).get("id") != code:
            issues["indicator_mismatch"] += 1
            continue
        try:
            year = int(r["date"])
        except (KeyError, TypeError, ValueError):
            issues["bad_year"].append(str(r.get("date")))
            continue
        if not start <= year <= end:
            issues["out_of_window"].append((iso3, year))
            continue
        raw = r.get("value")
        if raw is None:
            value = math.nan
        elif isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            issues["non_numeric"].append((iso3, year, str(raw)[:20]))
            continue
        else:
            value = float(raw)
        key = (iso3, code, year)
        if key in seen:
            issues["duplicates"].append(key)
            continue
        seen.add(key)
        rows.append(
            {
                "country_code": iso3,
                "indicator_code": code,
                "year": year,
                "value": value,
                "unit": unit,
                "source_name": SOURCE_NAME,
                "source_url": INDICATOR_URL.format(code=code),
                "footnote": (r.get("obs_status") or "").strip() or None,
                "observation_status": "missing" if math.isnan(value) else "reported",
                "retrieved_at": retrieved_at,
            }
        )
    return pd.DataFrame(rows), issues


def count_issues(issues: dict) -> int:
    return sum(len(v) if isinstance(v, list) else v for v in issues.values())
