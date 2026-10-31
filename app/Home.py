import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

import streamlit as st  # noqa: E402
from components import charts, ui  # noqa: E402
from components.data import Data  # noqa: E402
from components.domain_page import transformed  # noqa: E402

KPI_CODES = [
    "SP.POP.TOTL", "NY.GDP.MKTP.CD", "NY.GDP.PCAP.CD", "NY.GDP.MKTP.KD.ZG",
    "SP.URB.TOTL.IN.ZS", "NV.AGR.TOTL.ZS", "SP.DYN.LE00.IN", "IT.NET.USER.ZS",
]
HIGHLIGHTS = [
    ("SP.POP.TOTL", "Population"), ("SP.DYN.LE00.IN", "Life expectancy at birth"),
    ("SP.URB.TOTL.IN.ZS", "Urban share of population"), ("NY.GDP.PCAP.CD", "GDP per capita (nominal)"),
    ("SL.AGR.EMPL.ZS", "Share of employment in agriculture"), ("EG.ELC.ACCS.ZS", "Access to electricity"),
]


def highlight(d: Data, code: str, label: str) -> str | None:
    """Computed from the database: first vs latest reported value, each with its own year. Nothing is typed in."""
    s = d.series("KHM", code).dropna()
    if len(s) < 2:
        return None
    (y0, v0), (y1, v1) = (int(s.index[0]), s.iloc[0]), (int(s.index[-1]), s.iloc[-1])
    f = lambda v: ui.fmt_value(v, d.unit(code), d.kind(code))  # noqa: E731
    delta = v1 - v0
    if d.kind(code) == "percent":
        change = f"{delta:+.1f} percentage points"
    elif v0 > 0:
        change = f"x{v1 / v0:.2f}"
    else:
        change = f"{delta:+,.2f}"
    return f"**{label}**: {f(v0)} in {y0} -> {f(v1)} in {y1} ({change}; {d.unit(code)})."


d = ui.setup("National Overview", "🇰🇭")
ui.header("Cambodia Public Statistics Intelligence",
          "An integrated national and ASEAN development data observatory, built on World Bank World Development Indicators.")

s = d.summary
st.caption(f"{s['reported']:,} reported values of {s['rows']:,} country-indicator-year cells "
           f"({len(d.countries)} countries, {len(d.indicators)} indicators, {d.start}-{d.end}). "
           f"Data retrieved {s['last_retrieved']:%Y-%m-%d}. Each card shows the LATEST REPORTED year for that indicator, "
           "which differs between indicators.")

cols = st.columns(4)
for i, code in enumerate(KPI_CODES):
    with cols[i % 4]:
        ui.kpi_card(d, "KHM", code)

left, right = st.columns([3, 2])
with left:
    st.subheader("Historical development")
    code = st.selectbox("Indicator", d.indicators.indicator_code, index=list(d.indicators.indicator_code).index("NY.GDP.PCAP.CD"),
                        format_func=d.name, key="home_ind")
    extra = st.multiselect("Add countries for context", [c for c in d.countries.iso3 if c != "KHM"], format_func=d.cname, key="home_extra")
    cs = ["KHM", *extra]
    f, ylabel, how = transformed(d, code, cs, "Reported values", d.start, d.end)
    st.plotly_chart(charts.trend_fig(f, {c: d.cname(c) for c in cs}, ylabel, d.name(code)), width="stretch")
    st.caption("Breaks in a line are years with no reported value. " + (d.ind(code).notes or ""))
    ui.source_box(d, code)
with right:
    st.subheader("Statistical highlights")
    st.caption("Computed from the database at page load: first vs latest reported value for Cambodia.")
    for code, label in HIGHLIGHTS:
        h = highlight(d, code, label)
        if h:
            st.markdown("- " + h)
    st.caption("GDP per capita is in current (nominal) US dollars, so it is not adjusted for inflation. "
               "Comparing two years' levels is not a real-growth measure.")

st.subheader("What is missing for Cambodia")
kd = d.dq[d.dq.country_code == "KHM"].copy()
kd["indicator"] = kd.indicator_code.map(d.name)
old = kd[(kd.latest_year.isna()) | (kd.latest_year < d.end - 2)]
st.markdown(f"**{int((kd.valid_observations > 0).sum())} of {len(kd)}** indicators have any observation; "
            f"**{len(old)}** have no value in the last three years ({d.end - 2}-{d.end}).")
st.dataframe(old[["indicator", "valid_observations", "first_year", "latest_year", "completeness_pct"]].rename(
    columns={"valid_observations": "reported years", "completeness_pct": "% of 1960-2025 reported"}),
    hide_index=True, width="stretch")

st.info("No map is shown: this project holds national-level indicators only, so there is nothing to map by province. "
        "Provincial data are listed under future work (docs/NEXT_STEPS.md).")
st.caption("Source: World Bank, World Development Indicators (see Data Quality and Methodology for licences). " + ui.DISCLAIMER)
