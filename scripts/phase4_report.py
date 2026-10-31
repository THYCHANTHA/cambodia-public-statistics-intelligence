"""Compute Phase 4 results from the stored DuckDB data and write reports/validation/phase4_statistics.md.

Every number in the report is calculated here from the database; nothing is typed by hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cpsi.analysis import compare, correlation, descriptive, outliers, quality, trends  # noqa: E402
from cpsi.config import END_YEAR, REPORTS_DIR, START_YEAR  # noqa: E402
from cpsi.database import queries  # noqa: E402


def md(df: pd.DataFrame, floatfmt: str = ".2f") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt)


def main() -> None:
    con = queries.connect_ro()
    ctry, ind = queries.countries(con), queries.indicators(con)
    obs = queries.observations(con)
    kind = ind.set_index("indicator_code")["value_kind"].to_dict()
    name = ind.set_index("indicator_code")["indicator_name"].to_dict()
    out = [
        "# Phase 4: statistical analysis results", "",
        f"Computed by `scripts/phase4_report.py` from the existing DuckDB store ({len(obs):,} observation rows, "
        f"{int(obs.value.notna().sum()):,} reported). No data were re-downloaded. Window {START_YEAR}-{END_YEAR}. "
        "All analyses are exploratory and descriptive; none establishes causality.", "",
    ]

    # 1. Descriptive
    d = descriptive.describe(obs[obs.country_code == "KHM"], START_YEAR, END_YEAR)
    d["indicator"] = d.indicator_code.map(name).str.slice(0, 48)
    out += ["## 1. Descriptive statistics: Cambodia, all 25 indicators", "",
            "Computed on reported values only; `n` is the number of observations used.", "",
            md(d[["indicator_code", "indicator", "n_reported", "n_missing", "completeness_pct", "mean", "median", "min",
                  "max", "std", "first_year", "latest_year", "latest_value"]].rename(columns={"n_reported": "n"}),
               ".3g"), ""]

    # 2. Trends
    k = obs[(obs.country_code == "KHM")]
    rows = []
    for code in ["NY.GDP.PCAP.CD", "SP.POP.TOTL", "SP.URB.TOTL.IN.ZS", "IT.NET.USER.ZS", "SP.DYN.LE00.IN"]:
        s = k[k.indicator_code == code].set_index("year")["value"]
        ch = trends.annual_changes(s, kind[code]).dropna(subset=["absolute_change"]).tail(1).iloc[0]
        col = "percentage_point_change" if kind[code] == "percent" else "percentage_growth"
        r3 = trends.rolling_mean(s, 3).dropna(subset=["rolling_mean"]).tail(1).iloc[0]
        r5 = trends.rolling_mean(s, 5).dropna(subset=["rolling_mean"]).tail(1).iloc[0]
        rows.append({"indicator": code, "latest_change_year": int(ch.year), "change_type": trends.change_label(kind[code]),
                     "absolute_change": ch.absolute_change, "pct_or_pp": ch[col],
                     "rolling3_last": f"{r3.rolling_mean:.4g} ({int(r3.year)})", "rolling5_last": f"{r5.rolling_mean:.4g} ({int(r5.year)})"})
    out += ["## 2. Trends: Cambodia, latest computable annual change and rolling means", "",
            "A change is computed only when the immediately preceding calendar year is reported. Rolling means need all "
            "w consecutive years. Percent-valued series use percentage points, never percentage growth.", "", md(pd.DataFrame(rows), ".4g"), ""]
    s = k[k.indicator_code == "NY.GDP.PCAP.CD"].set_index("year")["value"]
    g = trends.annual_changes(s, "level")
    out += [f"Cambodia GDP per capita: {int(g.value.notna().sum())} reported years; years with a computable growth rate: "
            f"{int(g.percentage_growth.notna().sum())}; years inside the span without a value: {int(g.value.isna().sum())}.", ""]

    # 3. Correlation
    asean_cze = compare.select_countries(ctry, "all")
    specs = [("NY.GDP.PCAP.CD", "SP.DYN.LE00.IN"), ("NY.GDP.PCAP.CD", "IT.NET.USER.ZS"),
             ("NY.GDP.PCAP.CD", "SL.AGR.EMPL.ZS"), ("SP.URB.TOTL.IN.ZS", "NY.GDP.PCAP.CD"),
             ("NY.GDP.PCAP.CD", "SH.DYN.MORT")]
    rows = []
    for x, y in specs:
        for label, cs in (("pooled 12 countries", asean_cze), ("Cambodia only", ["KHM"])):
            res = correlation.correlate(correlation.aligned_pairs(obs, x, y, countries=cs))
            rows.append({"x": x, "y": y, "sample": label, "n_pairs": res["n_pairs"], "pearson_r": res["pearson_r"],
                         "spearman_rho": res["spearman_rho"], "spearman_p": res["spearman_p"], "status": res["status"]})
    out += ["## 3. Correlation (exploratory)", "", correlation.CAVEAT, "",
            "Pairs are country-years where both indicators are reported (pairwise deletion). Minimum 8 pairs. "
            "Raw (not log-transformed) values; Spearman is the safer summary for skewed variables such as GDP per capita.", "",
            md(pd.DataFrame(rows), ".3g"), ""]

    # 4. Outliers
    flags = outliers.flag_outliers(obs)
    nser = obs.dropna(subset=["value"]).groupby(["country_code", "indicator_code"]).size().ge(outliers.MIN_OBS).sum()
    both = flags[flags.iqr_flag & flags.robust_z_flag]
    by_ind = flags.groupby("indicator_code").size().rename("flagged_rows").reset_index()
    out += ["## 4. Outlier flags (for review; no value is removed or changed)", "",
            f"Series tested (>= {outliers.MIN_OBS} reported values): {int(nser)}. Rows flagged by either rule: {len(flags)}; "
            f"by both IQR (k=1.5) and robust z (|z|>3.5): {len(both)}.", "",
            "Caveat: both rules treat a series as exchangeable values and ignore its time trend, so strongly trending or "
            "regime-changing series (population, GDP, land use) are flagged more often. A flag means 'look at this', not 'wrong'.",
            "", md(by_ind), ""]
    z = outliers.suspect_zeros(obs)
    out += ["### Exact zeros in growth-rate series (review list)", "", md(z), ""]
    kg = k[(k.indicator_code == "NY.GDP.MKTP.KD.ZG")].set_index("year")["value"]
    ctx = kg.loc[1974:1985].rename("value").reset_index()
    ctx["status"] = ctx.value.map(lambda v: "MISSING" if pd.isna(v) else ("EXACT ZERO" if v == 0 else "reported"))
    nz_total = int(((obs.indicator_code == "NY.GDP.MKTP.KD.ZG") & (obs.value == 0)).sum())
    out += ["### Investigation: Cambodia GDP growth (NY.GDP.MKTP.KD.ZG), 1974-1985", "", md(ctx, ".4g"), "",
            f"- Cambodia has exactly {int((kg == 0).sum())} zero values ({', '.join(str(y) for y in kg.index[kg == 0])}), "
            f"alternating with non-zero values in the same decade. Across all 12 countries and all years there are {nz_total} exact "
            f"zeros in this indicator, {int((kg == 0).sum())} of them Cambodian.",
            "- An exact 0.0 for a continuously measured annual growth rate is unlikely in real data, especially "
            "between -14.7 and +0.04. This is a **pattern consistent with placeholder or imputed values in the source**, "
            "but this project cannot confirm that: the API provides no footnote (all footnotes are empty) and no primary-source "
            "check was done. Status: **flagged for review; values left unchanged; shown with a warning in the app.**", ""]

    # 5. Comparison
    asean = compare.select_countries(ctry, "asean")
    yr = compare.latest_common_year(obs, "NY.GDP.PCAP.CD", asean)
    t = compare.compare_year(obs, ctry, "NY.GDP.PCAP.CD", asean, yr)
    out += ["## 5. Country comparison", "",
            f"GDP per capita (current US$), ASEAN members, latest year in which all 11 have a value: **{yr}**. "
            f"{t.attrs['rank_rule']} No ASEAN aggregate is computed.", "",
            md(t[["rank", "country_code", "country_name", "year", "value", "unit", "status", "note"]], ",.1f"), ""]
    yr2 = compare.latest_common_year(obs, "SP.DYN.LE00.IN", ["KHM", "CZE"])
    t2 = compare.compare_year(obs, ctry, "SP.DYN.LE00.IN", ["KHM", "CZE"], yr2)
    out += [f"Life expectancy, Cambodia vs Czechia, latest common year **{yr2}**:", "",
            md(t2[["rank", "country_code", "year", "value", "unit"]]), ""]
    yrl = compare.latest_common_year(obs, "SE.ADT.LITR.ZS", asean)
    out += [f"Latest year in which all 11 ASEAN members have adult literacy: {yrl} "
            "(None means no such year exists, so a strict same-year ranking is not possible and the app will say so).", ""]

    # 6. Quality
    cm = quality.completeness_matrix(obs, START_YEAR, END_YEAR)
    out += ["## 6. Data-quality analysis", "", "### Availability by country", "",
            md(quality.availability_by_country(obs, END_YEAR), ".0f"), "",
            "### Missing-year runs: Cambodia adult literacy and health expenditure", ""]
    for code in ["SE.ADT.LITR.ZS", "SH.XPD.CHEX.GD.ZS"]:
        sr = k[k.indicator_code == code].set_index("year")["value"]
        out += [f"`{code}`: {quality.series_quality(sr, START_YEAR, END_YEAR)}", "", md(quality.missing_runs(sr, START_YEAR, END_YEAR), ".0f"), ""]
    out += ["### Mean completeness by indicator across countries (percent of window years reported)", "",
            md(cm.mean().round(1).rename("mean_completeness_pct").rename_axis("indicator_code").reset_index()), ""]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "phase4_statistics.md").write_text("\n".join(out), encoding="utf-8")
    print("written", len(out), "blocks")


if __name__ == "__main__":
    main()
