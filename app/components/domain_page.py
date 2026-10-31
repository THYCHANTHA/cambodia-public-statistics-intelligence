"""One renderer for the five thematic pages: KPI cards, trend, comparison, statistics, coverage, relationships, data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, ui
from components.data import Data
from cpsi.analysis import compare, correlation, descriptive, outliers, trends

MODES = ["Reported values", "Year-to-year change", "3-year rolling mean", "5-year rolling mean"]


def transformed(d: Data, code: str, countries: list[str], mode: str, start: int, end: int) -> tuple[pd.DataFrame, str, str]:
    """Return (frame country_code/year/y, y-axis label, plain-language description of the calculation).

    Changes and rolling means are computed on each country's FULL series, then cut to the selected years."""
    unit, kind = d.unit(code), d.kind(code)
    rows, how = [], ""
    for c in countries:
        s = d.series(c, code)
        if mode == "Reported values":
            f = pd.DataFrame({"year": s.index, "y": s.values})
            ylabel, how = unit, "Reported values exactly as published. Gaps are left as gaps."
        elif mode == "Year-to-year change":
            ch = trends.annual_changes(s, kind)
            if kind == "percent":
                f, ylabel = ch.rename(columns={"percentage_point_change": "y"})[["year", "y"]], "percentage points"
                how = "Percentage-point change = value(t) - value(t-1), shown only if year t-1 is reported."
            else:
                f, ylabel = ch.rename(columns={"percentage_growth": "y"})[["year", "y"]], "% change on previous year"
                how = ("Annual percentage growth = (value(t) / value(t-1) - 1) x 100, only if year t-1 is reported and "
                       "positive. Missing years are never bridged.")
        else:
            w = 3 if mode.startswith("3") else 5
            r = trends.rolling_mean(s, w)
            f, ylabel = r.rename(columns={"rolling_mean": "y"})[["year", "y"]], f"{unit} ({w}-yr rolling mean)"
            how = f"Mean of {w} consecutive calendar years ending in the plotted year; blank unless all {w} are reported."
        f = f[f.year.between(start, end)].assign(country_code=c)
        rows.append(f)
    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["year", "y", "country_code"])), ylabel, how


def relationships(d: Data, code: str, countries: list[str], start: int, end: int, key: str) -> None:
    st.caption("Exploratory analysis of aligned country-year pairs. " + correlation.CAVEAT)
    others = [c for c in d.indicators.indicator_code if c != code]
    other = st.selectbox("Compare with", others, format_func=d.name, key=f"{key}_rel_other")
    scope = st.radio("Sample", ["Selected countries pooled", "Cambodia only"], horizontal=True, key=f"{key}_rel_scope")
    cs = countries if scope.startswith("Selected") else ["KHM"]
    obs = d.slice([code, other], cs, start, end)
    pairs = correlation.aligned_pairs(obs, code, other)
    res = correlation.correlate(pairs)
    c1, c2, c3 = st.columns(3)
    c1.metric("Paired observations", res["n_pairs"])
    if res["status"] != "ok":
        st.warning(f"No coefficient shown: {res['status']}.")
    else:
        c2.metric("Pearson r", f"{res['pearson_r']:.3f}", help="Linear association; sensitive to outliers and skew.")
        c3.metric("Spearman rho", f"{res['spearman_rho']:.3f}", help="Rank (monotonic) association.")
        st.caption(f"Indicative p-values (independence assumption violated): Pearson {res['pearson_p']:.2g}, "
                   f"Spearman {res['spearman_p']:.2g}. Association, not causation.")
    if len(pairs):
        names = {c: d.cname(c) for c in pairs.country_code.unique()}
        st.plotly_chart(charts.scatter_fig(pairs, f"{d.name(code)} [{d.unit(code)}]", f"{d.name(other)} [{d.unit(other)}]",
                                           names, "Aligned country-year pairs"), width="stretch")
        ui.csv_button(pairs.rename(columns={"x": code, "y": other}), f"pairs_{code}_{other}.csv", key=f"{key}_rel_csv")


def render_domain(title: str, subtitle: str, domains: list[str], key: str, icon: str = "📊") -> None:
    d = ui.setup(title, icon)
    ui.header(title, subtitle)
    inds = d.indicators[d.indicators.domain.isin(domains)]
    codes = inds.indicator_code.tolist()

    st.markdown("##### Cambodia: latest reported value for each indicator")
    cols = st.columns(3)
    for i, code in enumerate(codes):
        with cols[i % 3]:
            ui.kpi_card(d, "KHM", code)

    with st.sidebar:
        st.markdown("#### Filters")
        code = st.selectbox("Indicator", codes, format_func=d.name, key=f"{key}_ind")
        countries = ui.country_picker(d, key)
        start, end = st.slider("Years", d.start, d.end, (d.start, d.end), key=f"{key}_years")
        mode = st.radio("Show", MODES, key=f"{key}_mode")
    if not countries:
        st.stop()

    st.subheader(d.name(code))
    row = d.ind(code)
    if row.notes:
        st.info(row.notes)
    z = outliers.suspect_zeros(d.slice([code], countries, start, end))
    if len(z):
        st.warning("Review flag: exact zero(s) in a growth-rate series, possibly source placeholders (values unchanged): "
                   + "; ".join(f"{d.cname(r.country_code)} {int(r.year)}" for r in z.itertuples()))

    tabs = st.tabs(["Trend", "Compare countries", "Statistics", "Data coverage", "Relationships", "Data & download"])

    with tabs[0]:
        f, ylabel, how = transformed(d, code, countries, mode, start, end)
        if f["y"].notna().sum() == 0:
            st.warning("No values can be shown for this selection (no reported observations, or no consecutive years).")
        st.plotly_chart(charts.trend_fig(f, {c: d.cname(c) for c in countries}, ylabel, f"{d.name(code)}: {mode.lower()}",
                                         zero_line=(mode == "Year-to-year change")), width="stretch")
        st.caption(how)
        used = descriptive.describe(d.slice([code], countries, start, end), start, end)
        st.markdown("**Observations behind this chart**")
        st.dataframe(used.assign(country=used.country_code.map(d.cname))[
            ["country", "n_reported", "n_missing", "completeness_pct", "first_year", "latest_year"]], hide_index=True, width="stretch")

    with tabs[1]:
        common = compare.latest_common_year(d.obs[d.obs.year.between(start, end)], code, countries)
        avail = sorted(d.slice([code], countries, start, end).dropna(subset=["value"]).year.unique())
        if not avail:
            st.warning("No reported values in the selected years.")
        else:
            default = common if common else avail[-1]
            if common is None:
                st.info("No single year has a value for every selected country; countries without a value in the chosen "
                        "year are listed as missing and are not ranked.")
            year = st.select_slider("Reference year", options=avail, value=default, key=f"{key}_cmp_year") if len(avail) > 1 else avail[0]
            t = compare.compare_year(d.slice([code], countries, d.start, d.end), d.countries, code, countries, int(year))
            st.plotly_chart(charts.rank_fig(t, d.unit(code), f"{d.name(code)}, {year}"), width="stretch")
            st.caption(t.attrs["rank_rule"] + " No regional aggregate is calculated.")
            show = t[["rank", "country_name", "year", "value", "unit", "status", "latest_reported_year", "note"]]
            st.dataframe(show, hide_index=True, width="stretch")
            ui.csv_button(show, f"comparison_{code}_{year}.csv", key=f"{key}_cmp_csv")

    with tabs[2]:
        ds = descriptive.describe(d.slice([code], countries, start, end), start, end)
        ds.insert(1, "country", ds.country_code.map(d.cname))
        st.caption(f"Statistics use only reported observations inside {start}-{end}; n is shown for every row. "
                   "Standard deviation is the sample SD and is blank when n < 2.")
        st.dataframe(ds.drop(columns=["country_code", "indicator_code", "window_start", "window_end"]), hide_index=True, width="stretch")
        ui.csv_button(ds, f"statistics_{code}.csv", key=f"{key}_stat_csv")

    with tabs[3]:
        st.plotly_chart(charts.coverage_fig(d.slice([code], countries, start, end), countries,
                                            {c: d.cname(c) for c in countries}, start, end,
                                            "Reported (blue) vs missing (grey) years"), width="stretch")
        st.caption("Grey means the source returned no value for that year. The API does not say whether a value was "
                   "not collected, not available or not applicable.")

    with tabs[4]:
        relationships(d, code, countries, start, end, key)

    with tabs[5]:
        data = d.slice([code], countries, start, end).copy()
        data["country"] = data.country_code.map(d.cname)
        wide = data.pivot(index="year", columns="country", values="value")
        st.dataframe(wide, width="stretch")
        st.caption("Blank cells are missing observations, not zeros.")
        out = data[["country_code", "country", "indicator_code", "year", "value", "unit", "observation_status",
                    "source_name", "retrieved_at"]]
        ui.csv_button(out, f"{code}_{start}_{end}.csv", key=f"{key}_data_csv")
        ui.source_box(d, code)
