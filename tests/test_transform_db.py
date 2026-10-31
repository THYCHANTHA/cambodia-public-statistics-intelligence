"""Transformation, quality and DuckDB tests on small synthetic data (no network)."""

from __future__ import annotations

import math

import duckdb
import pandas as pd
import pytest

from cpsi.config import load_countries, load_indicators, load_units
from cpsi.database import store
from cpsi.quality.completeness import completeness
from cpsi.transformation import observations as T

ISO = {"KHM", "THA"}


def rec(iso, year, value, code="X.Y", **extra):
    return {"indicator": {"id": code}, "countryiso3code": iso, "date": str(year), "value": value,
            "obs_status": "", **extra}


def parse(records, code="X.Y"):
    return T.parse_observations(records, code, ISO, "units", "2026-01-01T00:00:00+00:00", 2000, 2005)


def test_null_stays_missing_and_zero_stays_zero():
    df, issues = parse([rec("KHM", 2000, None), rec("KHM", 2001, 0), rec("KHM", 2002, 3.5)])
    assert T.count_issues(issues) == 0
    by_year = df.set_index("year")
    assert math.isnan(by_year.loc[2000, "value"]) and by_year.loc[2000, "observation_status"] == "missing"
    assert by_year.loc[2001, "value"] == 0 and by_year.loc[2001, "observation_status"] == "reported"


def test_duplicates_detected_not_silently_dropped():
    _, issues = parse([rec("KHM", 2000, 1), rec("KHM", 2000, 2)])
    assert issues["duplicates"] == [("KHM", "X.Y", 2000)]


@pytest.mark.parametrize("bad,key", [
    (rec("ZZZ", 2000, 1), "unknown_country"),
    (rec("KHM", "abc", 1), "bad_year"),
    (rec("KHM", 1990, 1), "out_of_window"),
    (rec("KHM", 2000, "12"), "non_numeric"),
    (rec("KHM", 2000, float("inf")), "non_numeric"),
    (rec("KHM", 2000, True), "non_numeric"),
])
def test_invalid_records_reported(bad, key):
    _, issues = parse([bad])
    assert issues[key]


def test_indicator_mismatch_reported():
    _, issues = parse([rec("KHM", 2000, 1, code="OTHER")])
    assert issues["indicator_mismatch"] == 1


def test_config_catalogue_is_consistent():
    inds, units = load_indicators(), load_units()
    codes = [i["code"] for i in inds]
    assert len(codes) == 25 and len(set(codes)) == 25
    assert set(codes) == set(units)
    assert "EN.ATM.CO2E.PC" not in codes and "EN.GHG.CO2.PC.CE.AR5" in codes
    assert all(units[c]["basis"] in ("name", "inferred") for c in codes)
    cs = load_countries()
    assert len(cs) == 12 and sum(c["group"] == "ASEAN" for c in cs) == 11
    assert next(c for c in cs if c["iso3"] == "CZE")["group"] == "EXTERNAL_BENCHMARK"


def _indicators(unit="% of population"):
    return pd.DataFrame({"indicator_code": ["X.Y"], "unit": [unit]})


def test_completeness_counts_gaps_and_staleness():
    obs = pd.DataFrame({"country_code": "KHM", "indicator_code": "X.Y",
                        "year": [2000, 2001, 2004], "value": [1.0, math.nan, 2.0]})
    dq = completeness(obs, ["KHM", "THA"], _indicators(), 2000, 2012, "t")
    khm = dq[dq.country_code == "KHM"].iloc[0]
    assert (khm.valid_observations, khm.missing_observations, khm.first_year, khm.latest_year) == (2, 11, 2000, 2004)
    assert khm.internal_gap_years == 3 and "older than" in khm.validation_warnings
    tha = dq[dq.country_code == "THA"].iloc[0]
    assert tha.valid_observations == 0 and tha.first_year is None or pd.isna(tha.first_year)
    assert "no observations" in tha.validation_warnings


def test_completeness_flags_implausible_values():
    obs = pd.DataFrame({"country_code": "KHM", "indicator_code": "X.Y", "year": [2000, 2001], "value": [-1.0, 120.0]})
    w = completeness(obs, ["KHM"], _indicators(), 2000, 2001, "t").iloc[0].validation_warnings
    assert "negative" in w and "above 100" in w


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    store.create_schema(c)
    store.load(c, "countries", pd.DataFrame([{
        "iso3": "KHM", "country_name": "Cambodia", "iso2": "KH", "world_bank_code": "KHM", "region": "r",
        "income_level": "i", "capital_city": "Phnom Penh", "country_group": "ASEAN", "asean_member_since": None,
        "source": "s", "retrieved_at": "2026-01-01T00:00:00+00:00"}]))
    store.load(c, "indicators", pd.DataFrame([{
        "indicator_code": "X.Y", "indicator_name": "n", "domain": "d", "unit": "u", "unit_basis": "name",
        "value_kind": "level", "estimate_type": None, "replaces_code": None, "definition": "d", "source_name": "s",
        "source_url": "u", "source_organization": "o", "frequency": "annual", "notes": None, "licence": "l",
        "retrieved_at": "2026-01-01T00:00:00+00:00"}]))
    return c


def _obs(**kw):
    base = {"country_code": "KHM", "indicator_code": "X.Y", "year": 2000, "value": 1.0, "unit": "u",
            "source_name": "s", "source_url": "u", "footnote": None, "observation_status": "reported",
            "retrieved_at": "2026-01-01T00:00:00+00:00"}
    return pd.DataFrame([{**base, **kw}])


def test_primary_key_rejects_duplicate(con):
    store.load(con, "observations", _obs())
    with pytest.raises(duckdb.ConstraintException):
        store.load(con, "observations", _obs(value=2.0))


def test_foreign_key_rejects_unknown_country(con):
    with pytest.raises(duckdb.ConstraintException):
        store.load(con, "observations", _obs(country_code="ZZZ"))


def test_status_value_consistency_enforced(con):
    with pytest.raises(duckdb.ConstraintException):
        store.load(con, "observations", _obs(value=math.nan, observation_status="reported"))


def test_nan_loads_as_null_and_query_roundtrip(con):
    store.load(con, "observations", pd.concat([_obs(year=2000, value=math.nan, observation_status="missing"),
                                               _obs(year=2001, value=0.0)]))
    rows = con.execute("SELECT year, value FROM observations ORDER BY year").fetchall()
    assert rows == [(2000, None), (2001, 0.0)]
