"""Cross-checks of the analysis functions against independent DuckDB SQL on the real stored data."""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

from cpsi.analysis import compare, correlation, descriptive, trends
from cpsi.config import DB_PATH, END_YEAR, START_YEAR
from cpsi.database import queries

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="DuckDB store not built")


@pytest.fixture(scope="module")
def con():
    c = queries.connect_ro()
    yield c
    c.close()


@pytest.fixture(scope="module")
def obs(con):
    return queries.observations(con)


def test_store_counts_match_ingestion_report(con):
    n, rep = con.execute("SELECT count(*), count(value) FROM observations").fetchone()
    assert (n, rep) == (19800, 13827)
    assert con.execute("SELECT count(*) FROM (SELECT 1 FROM observations GROUP BY source_name, country_code, "
                       "indicator_code, year HAVING count(*) > 1)").fetchone()[0] == 0


def test_descriptive_equals_sql_for_every_country_indicator(con, obs):
    d = descriptive.describe(obs, START_YEAR, END_YEAR).set_index(["country_code", "indicator_code"])
    sql = con.execute("SELECT country_code, indicator_code, count(value) n, avg(value) m, median(value) med, min(value) lo, "
                      "max(value) hi, stddev_samp(value) sd FROM observations GROUP BY ALL").df().set_index(
        ["country_code", "indicator_code"])
    assert len(d) == len(sql) == 300
    j = d.join(sql)
    assert (j.n_reported == j.n).all()
    for a, b in (("mean", "m"), ("median", "med"), ("min", "lo"), ("max", "hi"), ("std", "sd")):
        both = j[[a, b]].dropna()
        assert ((both[a] - both[b]).abs() <= 1e-9 * both[b].abs().clip(lower=1)).all(), a
        assert (j[a].isna() == j[b].isna()).all(), a


def test_growth_matches_sql_lag_on_consecutive_years(con, obs):
    s = obs[(obs.country_code == "KHM") & (obs.indicator_code == "NY.GDP.PCAP.CD")].set_index("year")["value"]
    got = trends.annual_changes(s, "level").set_index("year")["percentage_growth"].dropna()
    sql = con.execute("""SELECT year, (value / prev - 1) * 100 g FROM (
        SELECT year, value, lag(value) OVER (ORDER BY year) prev, lag(year) OVER (ORDER BY year) py
        FROM observations WHERE country_code='KHM' AND indicator_code='NY.GDP.PCAP.CD' AND value IS NOT NULL)
        WHERE py = year - 1 AND prev > 0""").df().set_index("year")["g"]
    assert set(got.index) == set(sql.index) and len(got) > 40
    assert ((got - sql.loc[got.index]).abs() < 1e-9).all()


def test_percentage_point_change_is_difference_not_growth(obs):
    s = obs[(obs.country_code == "KHM") & (obs.indicator_code == "SP.URB.TOTL.IN.ZS")].set_index("year")["value"]
    ch = trends.annual_changes(s, "percent").set_index("year")
    assert ch.loc[2025, "percentage_point_change"] == pytest.approx(s[2025] - s[2024])
    assert ch["percentage_growth"].isna().all()


def test_pearson_matches_numpy_on_real_pairs(obs):
    p = correlation.aligned_pairs(obs, "NY.GDP.PCAP.CD", "SP.DYN.LE00.IN")
    res = correlation.correlate(p)
    assert res["n_pairs"] == len(p) >= 8
    assert res["pearson_r"] == pytest.approx(float(p["x"].corr(p["y"])), abs=1e-12)
    assert res["spearman_rho"] == pytest.approx(float(p["x"].corr(p["y"], method="spearman")), abs=1e-12)


def test_comparison_never_invents_values_or_aggregates(obs):
    ctry = pd.DataFrame({"iso3": ["KHM", "THA", "MMR"], "country_name": ["Cambodia", "Thailand", "Myanmar"],
                         "country_group": ["ASEAN"] * 3, "asean_member_since": [pd.NaT] * 3})
    t = compare.compare_year(obs, ctry, "NE.EXP.GNFS.ZS", ["KHM", "THA", "MMR"], 2020)
    mmr = t[t.country_code == "MMR"].iloc[0]
    assert math.isnan(mmr.value) and mmr.status == "missing in this year" and math.isnan(mmr["rank"])
    assert set(t.country_code) == {"KHM", "THA", "MMR"}


def test_csv_export_keeps_missing_blank_and_zero_zero(obs):
    sub = obs[(obs.country_code == "KHM") & (obs.indicator_code == "NY.GDP.MKTP.KD.ZG") & obs.year.between(1975, 1978)]
    back = pd.read_csv(io.StringIO(sub.to_csv(index=False)))
    by = back.set_index("year")["value"]
    assert math.isnan(by[1975]) and by[1976] == 0.0 and by[1977] < 0  # blank stays blank; observed zero stays 0
    assert "unit" in back.columns and "source_name" in back.columns and "retrieved_at" in back.columns


def test_zero_growth_values_are_preserved_unchanged(con):
    z = con.execute("SELECT year FROM observations WHERE country_code='KHM' AND indicator_code='NY.GDP.MKTP.KD.ZG' "
                    "AND value = 0 ORDER BY year").fetchall()
    assert [r[0] for r in z] == [1976, 1978, 1982]


def test_app_modules_import_cleanly():
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root / "app")]
    from components import charts, data, domain_page, ui  # noqa: F401
