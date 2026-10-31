import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from components import charts, ui  # noqa: E402
from components.domain_page import MODES, relationships, transformed  # noqa: E402

from cpsi.analysis import compare  # noqa: E402

d = ui.setup("ASEAN Comparison", "🌏")
ui.header("ASEAN Comparison", "Cambodia against the 11 ASEAN members, with Czechia as an optional external benchmark.")
st.warning("Rankings use ONE reference year and only countries with a reported value in that year. No ASEAN or regional "
           "average is calculated or shown: an unweighted mean of country values is not an official regional statistic.")

with st.sidebar:
    st.markdown("#### Filters")
    code = st.selectbox("Indicator", d.indicators.indicator_code, key="cmp_ind",
                        index=list(d.indicators.indicator_code).index("NY.GDP.PCAP.CD"),
                        format_func=lambda c: f"{d.ind(c).domain.replace('_', ' ').title()} · {d.name(c)}")
    countries = ui.country_picker(d, "cmp")
    start, end = st.slider("Years", d.start, d.end, (d.start, d.end), key="cmp_years")
    mode = st.radio("Trend view", MODES, key="cmp_mode")
if not countries:
    st.stop()

st.subheader(d.name(code))
if d.ind(code).notes:
    st.info(d.ind(code).notes)
tabs = st.tabs(["Ranking for one year", "Trends", "Differences from Cambodia", "Data coverage", "Relationships"])

sub = d.slice([code], countries, d.start, d.end)
avail = sorted(sub[sub.year.between(start, end)].dropna(subset=["value"]).year.unique())
common = compare.latest_common_year(sub[sub.year.between(start, end)], code, countries)

with tabs[0]:
    if not avail:
        st.warning("No reported values in the selected years for these countries.")
    else:
        if common is None:
            st.info("There is no year in which every selected country reports this indicator, so a complete same-year ranking "
                    "is impossible. Pick a year: countries without a value are shown as missing and are not ranked.")
        else:
            st.success(f"Latest year in which all {len(countries)} selected countries report a value: {common}.")
        mode_year = st.radio("Reference year", ["Latest common year", "Choose a year"], horizontal=True, key="cmp_yearmode",
                             index=0 if common else 1)
        if mode_year == "Latest common year" and common:
            year = common
        else:
            year = st.select_slider("Year", options=avail, value=avail[-1], key="cmp_year") if len(avail) > 1 else avail[0]
        t = compare.compare_year(sub, d.countries, code, countries, int(year))
        st.plotly_chart(charts.rank_fig(t, d.unit(code), f"{d.name(code)}, {year}"), width="stretch")
        st.caption(t.attrs["rank_rule"])
        miss = t[t.value.isna()]
        if len(miss):
            st.markdown("**No value in " + str(year) + ":** " + ", ".join(
                f"{r.country_name} (latest reported: {int(r.latest_reported_year) if pd.notna(r.latest_reported_year) else 'never'})"
                for r in miss.itertuples()))
        shown = t[["rank", "country_name", "year", "value", "unit", "status", "latest_reported_year", "note"]]
        st.dataframe(shown, hide_index=True, width="stretch")
        ui.csv_button(shown, f"asean_comparison_{code}_{year}.csv", key="cmp_csv")

with tabs[1]:
    f, ylabel, how = transformed(d, code, countries, mode, start, end)
    st.plotly_chart(charts.trend_fig(f, {c: d.cname(c) for c in countries}, ylabel, f"{d.name(code)}: {mode.lower()}"),
                    width="stretch")
    st.caption(how + " Different countries have different first and latest years; nothing is aligned or filled.")

with tabs[2]:
    if not avail:
        st.warning("No reported values.")
    else:
        y2 = st.select_slider("Year", options=avail, value=avail[-1], key="cmp_diff_year") if len(avail) > 1 else avail[0]
        t = compare.compare_year(sub, d.countries, code, countries, int(y2))
        base = t.loc[t.country_code == "KHM", "value"]
        if "KHM" not in countries or base.empty or base.isna().all():
            st.info(f"Cambodia has no reported value in {y2} (or is not selected), so differences cannot be computed.")
        else:
            t["difference_from_cambodia"] = t["value"] - base.iloc[0]
            t["unit_of_difference"] = d.unit(code) if d.kind(code) != "percent" else "percentage points"
            st.dataframe(t[["country_name", "value", "difference_from_cambodia", "unit_of_difference", "status"]],
                         hide_index=True, width="stretch")
            st.caption("Difference = country value minus Cambodia's value, same indicator and same year. "
                       "Descriptive only; countries differ in size, income and measurement systems.")

with tabs[3]:
    st.plotly_chart(charts.coverage_fig(sub[sub.year.between(start, end)], countries, {c: d.cname(c) for c in countries},
                                        start, end, "Reported (blue) vs missing (grey) years"), width="stretch")
    if "TLS" in countries:
        st.caption("Timor-Leste became an ASEAN member on 2025-10-26; earlier observations predate its membership.")

with tabs[4]:
    relationships(d, code, countries, start, end, "cmp")

ui.source_box(d, code)
