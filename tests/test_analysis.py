"""Deterministic tests for the statistical module. Expected values are computed by hand in the comments."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from cpsi.analysis import compare, correlation, descriptive, outliers, quality, trends


def series(d):
    return pd.Series(d, dtype=float).rename_axis("year")


# ---------- descriptive ----------
def test_descriptive_uses_only_reported_values():
    s = series({2000: 2.0, 2001: np.nan, 2002: 4.0, 2003: 6.0})
    d = descriptive.describe_series(s, 2000, 2004)  # window of 5 years, 3 reported
    assert (d["n_reported"], d["n_missing"], d["window_years"]) == (3, 2, 5)
    assert d["completeness_pct"] == 60.0
    assert d["mean"] == 4.0 and d["median"] == 4.0 and d["min"] == 2.0 and d["max"] == 6.0
    assert d["std"] == pytest.approx(2.0)  # sample sd of 2,4,6
    assert (d["first_year"], d["latest_year"], d["latest_value"]) == (2000, 2003, 6.0)


def test_descriptive_respects_window_and_handles_empty_or_single():
    s = series({1990: 100.0, 2000: 1.0})
    assert descriptive.describe_series(s, 1995, 2005)["n_reported"] == 1
    d = descriptive.describe_series(s, 1995, 2005)
    assert math.isnan(d["std"]) and d["mean"] == 1.0  # std undefined for n=1
    e = descriptive.describe_series(series({}), 2000, 2002)
    assert e["n_reported"] == 0 and math.isnan(e["mean"]) and e["first_year"] is None


def test_describe_groups_long_table():
    obs = pd.DataFrame({"country_code": ["A", "A", "B"], "indicator_code": ["X"] * 3, "year": [2000, 2001, 2000],
                        "value": [1.0, 3.0, np.nan]})
    out = descriptive.describe(obs, 2000, 2001).set_index("country_code")
    assert out.loc["A", "mean"] == 2.0 and out.loc["B", "n_reported"] == 0


# ---------- growth / change ----------
def test_percentage_growth_for_level():
    out = trends.annual_changes(series({2000: 100.0, 2001: 110.0, 2002: 99.0}), "level").set_index("year")
    assert out.loc[2001, "percentage_growth"] == pytest.approx(10.0)  # 110/100 - 1
    assert out.loc[2002, "percentage_growth"] == pytest.approx(-10.0)  # 99/110 - 1
    assert out.loc[2002, "absolute_change"] == pytest.approx(-11.0)
    assert math.isnan(out.loc[2000, "percentage_growth"])  # no previous year
    assert out["percentage_point_change"].isna().all()


def test_percentage_point_change_for_percent_and_no_growth_pct():
    out = trends.annual_changes(series({2000: 40.0, 2001: 44.5}), "percent").set_index("year")
    assert out.loc[2001, "percentage_point_change"] == pytest.approx(4.5)  # NOT 11.25 % growth
    assert math.isnan(out.loc[2001, "percentage_growth"])
    assert trends.change_label("percent") == "percentage-point change"


def test_zero_or_negative_denominator_gives_no_growth():
    out = trends.annual_changes(series({2000: 0.0, 2001: 5.0, 2002: -2.0, 2003: 3.0}), "level").set_index("year")
    assert math.isnan(out.loc[2001, "percentage_growth"])  # previous = 0, no division
    assert out.loc[2001, "absolute_change"] == 5.0  # absolute change still defined
    assert math.isnan(out.loc[2003, "percentage_growth"])  # previous negative: ratio not meaningful
    assert not np.isinf(out["percentage_growth"].dropna()).any()


def test_missing_years_are_not_bridged():
    out = trends.annual_changes(series({2000: 100.0, 2003: 130.0, 2004: 143.0}), "level").set_index("year")
    assert out.loc[2001:2002, "value"].isna().all()
    assert math.isnan(out.loc[2003, "absolute_change"])  # 2002 missing, so no change 2000 -> 2003
    assert out.loc[2004, "percentage_growth"] == pytest.approx(10.0)


# ---------- rolling ----------
def test_rolling_mean_requires_full_consecutive_window():
    s = series({2000: 1.0, 2001: 2.0, 2002: 3.0, 2004: 5.0, 2005: 6.0, 2006: 7.0})  # 2003 missing
    r = trends.rolling_mean(s, 3).set_index("year")
    assert r.loc[2002, "rolling_mean"] == pytest.approx(2.0)
    assert math.isnan(r.loc[2003, "rolling_mean"]) and math.isnan(r.loc[2004, "rolling_mean"])
    assert math.isnan(r.loc[2005, "rolling_mean"])  # window 2003-2005 contains the gap
    assert r.loc[2006, "rolling_mean"] == pytest.approx(6.0)
    assert r.loc[2005, "n_observations_in_window"] == 2
    assert trends.rolling_mean(s, 5)["rolling_mean"].isna().all()  # no 5 consecutive years exist


def test_rolling_rejects_tiny_window():
    with pytest.raises(ValueError):
        trends.rolling_mean(series({2000: 1.0}), 1)


# ---------- correlation ----------
def _obs(xs, ys, country="A"):
    n = len(xs)
    years = list(range(2000, 2000 + n))
    return pd.concat([
        pd.DataFrame({"country_code": country, "indicator_code": "X", "year": years, "value": xs}),
        pd.DataFrame({"country_code": country, "indicator_code": "Y", "year": years, "value": ys}),
    ])


def test_pearson_spearman_known_values():
    x = list(range(1, 11))
    perfect = correlation.correlate(correlation.aligned_pairs(_obs(x, [2 * v + 1 for v in x]), "X", "Y"))
    assert perfect["pearson_r"] == pytest.approx(1.0) and perfect["spearman_rho"] == pytest.approx(1.0)
    mono = correlation.correlate(correlation.aligned_pairs(_obs(x, [v**3 for v in x]), "X", "Y"))
    assert mono["spearman_rho"] == pytest.approx(1.0) and mono["pearson_r"] < 1.0  # monotone, non-linear
    neg = correlation.correlate(correlation.aligned_pairs(_obs(x, [-v for v in x]), "X", "Y"))
    assert neg["pearson_r"] == pytest.approx(-1.0) and "causality" in neg["caveat"]


def test_pairwise_deletion_and_minimum_pairs():
    xs = [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    ys = [2.0, 4.0, 6.0, np.nan, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    p = correlation.aligned_pairs(_obs(xs, ys), "X", "Y")
    assert len(p) == 8  # rows 3 and 4 dropped pairwise
    assert correlation.correlate(p)["status"] == "ok"
    short = correlation.correlate(p.iloc[:7])
    assert short["n_pairs"] == 7 and "insufficient" in short["status"] and math.isnan(short["pearson_r"])


def test_constant_input_is_undefined_not_error():
    res = correlation.correlate(correlation.aligned_pairs(_obs([1.0] * 10, list(range(10))), "X", "Y"))
    assert "constant" in res["status"] and math.isnan(res["pearson_r"])


def test_pooled_pairs_align_on_country_and_year():
    o = pd.concat([_obs(list(range(1, 10)), list(range(1, 10)), "A"), _obs(list(range(1, 10)), [9] * 9, "B")])
    assert len(correlation.aligned_pairs(o, "X", "Y")) == 18
    assert len(correlation.aligned_pairs(o, "X", "Y", countries=["A"], start=2003)) == 6
    by = correlation.correlate_by_country(correlation.aligned_pairs(o, "X", "Y")).set_index("country_code")
    assert by.loc["A", "pearson_r"] == pytest.approx(1.0) and "constant" in by.loc["B", "status"]


# ---------- outliers ----------
def test_iqr_and_robust_z_flag_without_changing_data():
    vals = [10, 11, 12, 11, 10, 12, 11, 10, 12, 11, 100.0]
    obs = pd.DataFrame({"country_code": "A", "indicator_code": "X", "year": range(2000, 2011), "value": vals})
    before = obs.copy()
    f = outliers.flag_outliers(obs)
    assert list(f.year) == [2010] and f.iqr_flag.all() and f.robust_z_flag.all()
    pd.testing.assert_frame_equal(obs, before)  # input untouched


def test_outliers_skip_short_series_and_zero_mad():
    short = pd.DataFrame({"country_code": "A", "indicator_code": "X", "year": range(2000, 2005), "value": [1, 1, 1, 1, 99.0]})
    assert outliers.flag_outliers(short).empty
    flat = pd.Series([5.0] * 9 + [6.0])
    assert outliers.robust_z(flat).isna().all()  # MAD = 0 -> undefined, not infinite


def test_suspect_zero_flagging_keeps_value():
    obs = pd.DataFrame({"country_code": ["KHM", "KHM", "KHM"], "indicator_code": ["NY.GDP.MKTP.KD.ZG"] * 2 + ["SP.POP.TOTL"],
                        "year": [1976, 1977, 1976], "value": [0.0, -14.7, 0.0]})
    z = outliers.suspect_zeros(obs)
    assert list(z.year) == [1976] and z.value.iloc[0] == 0.0  # population zero is not in the growth-rate list


# ---------- comparison ----------
@pytest.fixture
def meta():
    return pd.DataFrame({
        "iso3": ["KHM", "THA", "TLS", "CZE"], "country_name": ["Cambodia", "Thailand", "Timor-Leste", "Czechia"],
        "country_group": ["ASEAN", "ASEAN", "ASEAN", "EXTERNAL_BENCHMARK"],
        "asean_member_since": [pd.NaT, pd.NaT, pd.Timestamp("2025-10-26"), pd.NaT]})


@pytest.fixture
def cobs():
    rows = [("KHM", 2020, 10.0), ("THA", 2020, 30.0), ("TLS", 2020, 20.0), ("CZE", 2020, np.nan),
            ("KHM", 2019, 9.0), ("CZE", 2019, 99.0), ("THA", 2019, 29.0), ("TLS", 2019, 19.0)]
    return pd.DataFrame(rows, columns=["country_code", "year", "value"]).assign(indicator_code="X", unit="u")


def test_compare_ranks_only_matching_year_and_keeps_missing(meta, cobs):
    t = compare.compare_year(cobs, meta, "X", ["KHM", "THA", "TLS", "CZE"], 2020)
    assert list(t.country_code[:3]) == ["THA", "TLS", "KHM"] and list(t["rank"][:3]) == [1, 2, 3]
    cze = t[t.country_code == "CZE"].iloc[0]
    assert math.isnan(cze["rank"]) and cze.status == "missing in this year" and cze.latest_reported_year == 2019
    assert t.n_ranked.iloc[0] == 3 and "Not a quality judgement" in t.attrs["rank_rule"]
    assert "External benchmark" in cze.note
    assert "before ASEAN membership" in t[t.country_code == "TLS"].iloc[0].note


def test_latest_common_year(cobs):
    assert compare.latest_common_year(cobs, "X", ["KHM", "THA", "TLS", "CZE"]) == 2019
    assert compare.latest_common_year(cobs, "X", ["KHM", "THA"]) == 2020
    assert compare.latest_common_year(cobs, "X", ["KHM", "ZZZ"]) is None


def test_selection_groups_and_no_aggregate_row(meta, cobs):
    assert compare.select_countries(meta, "asean") == ["KHM", "THA", "TLS"]
    assert compare.select_countries(meta, "khm_vs_cze") == ["KHM", "CZE"]
    assert compare.select_countries(meta, "all") == meta.iso3.tolist()
    with pytest.raises(ValueError):
        compare.select_countries(meta, "nope")
    t = compare.compare_year(cobs, meta, "X", ["KHM", "THA"], 2020)
    assert set(t.country_code) == {"KHM", "THA"}  # no synthetic 'ASEAN' row


# ---------- quality ----------
def test_completeness_matrix_and_series_quality():
    obs = pd.DataFrame({"country_code": ["A", "A", "B"], "indicator_code": ["X", "X", "X"], "year": [2000, 2001, 2000],
                        "value": [1.0, np.nan, 2.0]})
    m = quality.completeness_matrix(obs, 2000, 2003)
    assert m.loc["A", "X"] == 25.0 and m.loc["B", "X"] == 25.0
    q = quality.series_quality(series({2000: 1.0, 2003: 2.0}), 2000, 2012)
    assert q["internal_gap_years"] == 2 and q["stale"] and q["completeness_pct"] == pytest.approx(15.38)
    assert quality.series_quality(series({}), 2000, 2012)["stale"]


def test_missing_runs_types():
    s = series({2002: 1.0, 2003: 1.0, 2006: 1.0})
    r = quality.missing_runs(s, 2000, 2008)
    assert r.to_dict("records") == [
        {"first_missing_year": 2000, "last_missing_year": 2001, "length": 2, "type": "leading"},
        {"first_missing_year": 2004, "last_missing_year": 2005, "length": 2, "type": "internal"},
        {"first_missing_year": 2007, "last_missing_year": 2008, "length": 2, "type": "trailing"}]
    assert quality.missing_runs(series({}), 2000, 2002).type.tolist() == ["all missing"]


def test_availability_and_historical_coverage():
    obs = pd.DataFrame({"country_code": ["A", "A", "B", "B"], "indicator_code": ["X", "Y", "X", "Y"],
                        "year": [2024, 1965, 1965, 1965], "value": [1.0, 2.0, np.nan, 3.0]})
    av = quality.availability_by_country(obs, 2025).set_index("country_code")
    assert av.loc["A", "indicators_with_any_data"] == 2 and av.loc["A", "indicators_with_recent_data"] == 1
    assert av.loc["B", "indicators_with_any_data"] == 1
    hc = quality.historical_coverage(obs).query("decade == '1960s'").set_index("indicator_code")
    assert hc.loc["X", "coverage_pct"] == 0.0 and hc.loc["Y", "coverage_pct"] == 100.0
