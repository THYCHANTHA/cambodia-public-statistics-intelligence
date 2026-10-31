import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from components import charts, ui  # noqa: E402

from cpsi.analysis import outliers, quality  # noqa: E402

d = ui.setup("Data Quality and Methodology", "🧪")
ui.header("Data Quality and Methodology", "How complete the data are, where they are missing, and how everything is calculated.")


@st.cache_data(show_spinner="Computing outlier flags...")
def flags(obs: pd.DataFrame):
    return outliers.flag_outliers(obs), outliers.suspect_zeros(obs)


def doc(name: str) -> str:
    p = ROOT / "docs" / name
    return p.read_text(encoding="utf-8") if p.exists() else f"*{name} not found.*"


s = d.summary
total, rep = s["rows"], s["reported"]
c = st.columns(4)
c[0].metric("Country-indicator-year cells", f"{total:,}")
c[1].metric("Reported values", f"{rep:,}")
c[2].metric("Missing (NULL)", f"{total - rep:,}")
c[3].metric("Coverage", f"{100 * rep / total:.1f}%")
st.caption("Missing values are stored as NULL and never replaced by zero, interpolated or forward-filled.")

tabs = st.tabs(["Completeness", "Missing-data patterns", "Historical coverage", "Country availability", "Review flags",
                "Methodology", "Sources and licences", "Limitations"])
names = {c: d.name(c) for c in d.indicators.indicator_code}
cnames = {i: d.cname(i) for i in d.countries.iso3}

with tabs[0]:
    cm = quality.completeness_matrix(d.obs, d.start, d.end)
    st.plotly_chart(charts.completeness_heatmap(cm, names, cnames, f"% of years {d.start}-{d.end} with a reported value"),
                    width="stretch")
    st.caption("Grey = no value in any year. Hover for the indicator name.")
    dq = d.dq.copy()
    dq["country"] = dq.country_code.map(cnames)
    dq["indicator"] = dq.indicator_code.map(names)
    sel = st.multiselect("Filter table by country", list(cnames), format_func=cnames.get, key="dq_c")
    only = st.checkbox("Only series with warnings", key="dq_w")
    view = dq[dq.country_code.isin(sel)] if sel else dq
    view = view[view.validation_warnings.notna()] if only else view
    cols = ["country", "indicator", "valid_observations", "missing_observations", "completeness_pct", "first_year",
            "latest_year", "internal_gap_years", "validation_warnings"]
    st.dataframe(view[cols], hide_index=True, width="stretch")
    ui.csv_button(view[cols], "data_quality.csv", key="dq_csv")

with tabs[1]:
    a, b = st.columns(2)
    cty = a.selectbox("Country", list(cnames), index=list(cnames).index("KHM"), format_func=cnames.get, key="mp_c")
    ind = b.selectbox("Indicator", list(names), index=list(names).index("SE.ADT.LITR.ZS"), format_func=names.get, key="mp_i")
    sr = d.series(cty, ind)
    q = quality.series_quality(sr, d.start, d.end)
    m = st.columns(4)
    m[0].metric("Reported years", q["n_reported"])
    m[1].metric("Completeness", f"{q['completeness_pct']}%")
    m[2].metric("First / latest year", f"{q['first_year'] or '-'} / {q['latest_year'] or '-'}")
    m[3].metric("Internal gap years", q["internal_gap_years"])
    if q["stale"]:
        st.warning(f"Stale: {q['stale_reason']}")
    runs = quality.missing_runs(sr, d.start, d.end)
    st.plotly_chart(charts.coverage_fig(d.slice([ind], [cty], d.start, d.end), [cty], cnames, d.start, d.end,
                                        f"{cnames[cty]}: {names[ind]}"), width="stretch")
    st.markdown("**Runs of consecutive missing years** (leading = before the first observation, trailing = after the latest)")
    st.dataframe(runs, hide_index=True, width="stretch")

with tabs[2]:
    hc = quality.historical_coverage(d.obs)
    piv = hc.pivot(index="indicator_code", columns="decade", values="coverage_pct").rename(index=names)
    st.caption("Percent of country-year cells reported, by decade (12 countries). 2020s has only 6 years.")
    st.dataframe(piv.style.format("{:.0f}", na_rep="-").background_gradient(cmap="Blues", vmin=0, vmax=100), width="stretch")

with tabs[3]:
    av = quality.availability_by_country(d.obs, d.end)
    av["country"] = av.country_code.map(cnames)
    st.caption(f"'Recent' = a reported value in {d.end - 4}-{d.end}.")
    st.dataframe(av[["country", "indicators_with_any_data", "indicators_with_recent_data", "indicators_total"]],
                 hide_index=True, width="stretch")

with tabs[4]:
    fl, zz = flags(d.obs)
    st.markdown("**Exact zeros in growth-rate series** (possible placeholders; values unchanged)")
    zz = zz.assign(country=zz.country_code.map(cnames), indicator=zz.indicator_code.map(names))
    st.dataframe(zz[["country", "indicator", "year", "value", "review_note"]], hide_index=True, width="stretch")
    st.markdown(f"**Statistical outlier flags** ({len(fl)} rows; IQR k=1.5 and/or robust z > 3.5). A flag means 'look at this', "
                "not 'wrong': both rules ignore time trends.")
    fl = fl.assign(country=fl.country_code.map(cnames), indicator=fl.indicator_code.map(names))
    pick = st.multiselect("Filter by country", list(cnames), default=["KHM"], format_func=cnames.get, key="fl_c")
    shown = fl[fl.country_code.isin(pick)] if pick else fl
    st.dataframe(shown[["country", "indicator", "year", "value", "robust_z", "iqr_flag", "robust_z_flag"]],
                 hide_index=True, width="stretch")
    ui.csv_button(fl.drop(columns=["country", "indicator"]), "outlier_flags.csv", key="fl_csv")

with tabs[5]:
    st.markdown(doc("methodology.md"))
with tabs[6]:
    st.markdown(doc("data_sources.md"))
    st.dataframe(d.indicators[["indicator_code", "indicator_name", "source_organization", "licence"]], hide_index=True,
                 width="stretch")
with tabs[7]:
    st.markdown(doc("limitations.md"))
st.caption(ui.DISCLAIMER)
