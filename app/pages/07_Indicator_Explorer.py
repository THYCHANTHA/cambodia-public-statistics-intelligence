import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from components import ui  # noqa: E402

d = ui.setup("Indicator Explorer", "🔎")
ui.header("Indicator Explorer", "Search the 25-indicator catalogue and see what data exist, from when, and how complete they are.")

dq = d.dq
agg = dq.groupby("indicator_code").agg(
    reported=("valid_observations", "sum"), missing=("missing_observations", "sum"),
    first_year=("first_year", "min"), latest_year=("latest_year", "max"),
    countries_with_data=("valid_observations", lambda s: int((s > 0).sum())),
).reset_index()
agg["completeness_pct"] = (100 * agg.reported / (agg.reported + agg.missing)).round(1)
cat = d.indicators.merge(agg, on="indicator_code")
cat["domain_label"] = cat.domain.str.replace("_", " ").str.title()

c1, c2, c3 = st.columns([3, 2, 2])
q = c1.text_input("Search name, code or definition", placeholder="e.g. mortality, GDP, SP.POP")
dom = c2.multiselect("Domain", sorted(cat.domain_label.unique()))
only_sparse = c3.checkbox("Only series below 60% complete")

view = cat
if q:
    ql = q.lower()
    view = view[view.indicator_name.str.lower().str.contains(ql, regex=False) | view.indicator_code.str.lower().str.contains(ql, regex=False)
                | view.definition.str.lower().str.contains(ql, regex=False)]
if dom:
    view = view[view.domain_label.isin(dom)]
if only_sparse:
    view = view[view.completeness_pct < 60]

if view.empty:
    st.warning("No indicator matches these filters.")
    st.stop()

table = view[["indicator_name", "indicator_code", "domain_label", "unit", "source_organization", "first_year", "latest_year",
              "completeness_pct", "reported", "missing", "countries_with_data"]].rename(columns={
    "domain_label": "domain", "source_organization": "original data source", "completeness_pct": "% of country-years reported",
    "reported": "reported obs", "missing": "missing obs", "countries_with_data": "countries with data (of 12)"})
table["original data source"] = table["original data source"].str.slice(0, 70)
st.caption(f"{len(view)} of {len(cat)} indicators. Completeness = reported / (12 countries x 66 years). "
           "First/latest year are the earliest/latest years in which ANY country reports a value.")
st.dataframe(table, hide_index=True, width="stretch")
ui.csv_button(view.drop(columns=["domain_label"]), "indicator_catalogue.csv", "Download catalogue (CSV)", key="exp_cat")

st.divider()
pick = st.selectbox("Inspect one indicator", view.indicator_code, format_func=d.name, key="exp_pick")
r = d.ind(pick)
st.subheader(r.indicator_name)
st.markdown(f"`{pick}` · domain **{r.domain.replace('_', ' ')}** · unit **{r.unit}**")
ui.source_box(d, pick)

per = dq[dq.indicator_code == pick].copy()
per["country"] = per.country_code.map(d.cname)
st.markdown("**Coverage by country**")
st.dataframe(per[["country", "valid_observations", "missing_observations", "completeness_pct", "first_year", "latest_year",
                  "internal_gap_years", "validation_warnings"]], hide_index=True, width="stretch")
data = d.obs[d.obs.indicator_code == pick].copy()
data["country"] = data.country_code.map(d.cname)
data["note"] = data.value.map(lambda v: "missing observation" if pd.isna(v) else "")
ui.csv_button(data[["country_code", "country", "indicator_code", "year", "value", "unit", "observation_status", "source_name",
                    "retrieved_at"]], f"{pick}_all_countries.csv", f"Download all observations for {pick} (CSV)", key="exp_data")
