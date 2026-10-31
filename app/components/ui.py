"""Shared look and feel: CSS, KPI cards, country picker, download buttons, attribution."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components import data as data_mod
from cpsi.analysis import compare

NAVY, BLUE, LIGHT, GREY = "#0B1F3A", "#2F80C9", "#E8F3FC", "#E5E7EB"
DISCLAIMER = (
    "Independent educational and research project. Not an official product of the Government of Cambodia, "
    "the National Institute of Statistics, the World Bank or ASEAN."
)

CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: 'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif; }}
h1, h2, h3 {{ color: {NAVY}; letter-spacing: -0.01em; }}
[data-testid="stSidebar"] {{ background: #F2F8FD; border-right: 1px solid #D6E8F7; }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
.hero {{ border-left: 5px solid {BLUE}; padding: .2rem 0 .2rem 1rem; margin-bottom: 1rem; animation: fadeUp .5s ease both; }}
.hero h1 {{ margin: 0; font-size: 2rem; }}
.hero p {{ margin: .25rem 0 0; color: #3A4F6B; }}
.kpi {{ background: #fff; border: 1px solid #D6E8F7; border-top: 4px solid {BLUE}; border-radius: 10px;
        padding: .8rem 1rem; margin-bottom: .8rem; min-height: 158px; animation: fadeUp .5s ease both;
        transition: box-shadow .2s ease, transform .2s ease; }}
.kpi:hover {{ box-shadow: 0 4px 14px rgba(47,128,201,.18); transform: translateY(-2px); }}
.kpi.empty {{ border-top-color: #9CA3AF; border-style: dashed; background: #F9FAFB; }}
.kpi .lbl {{ font-size: .8rem; color: #3A4F6B; font-weight: 600; min-height: 2.3em; }}
.kpi .val {{ font-size: 1.7rem; font-weight: 700; color: {NAVY}; line-height: 1.2; }}
.kpi .unit {{ font-size: .78rem; color: #3A4F6B; }}
.kpi .meta {{ font-size: .74rem; color: #5B6B82; margin-top: .35rem; }}
.badge {{ display: inline-block; font-size: .68rem; padding: 1px 7px; border-radius: 999px; margin-right: 4px;
          background: {LIGHT}; color: #1B4F8A; border: 1px solid #BBD9F2; }}
.badge.warn {{ background: #FFF4E0; color: #8A5A00; border-color: #F2D49B; }}
.badge.none {{ background: {GREY}; color: #374151; border-color: #D1D5DB; }}
.note {{ font-size: .8rem; color: #5B6B82; }}
</style>
"""


def setup(title: str, icon: str = "📊") -> data_mod.Data:
    st.set_page_config(page_title=f"{title} | Cambodia Public Statistics Intelligence", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### Cambodia Public Statistics Intelligence")
        st.caption(DISCLAIMER)
    try:
        return data_mod.load()
    except FileNotFoundError as exc:
        st.error(f"{exc}")
        st.stop()
    except Exception as exc:  # noqa: BLE001 - show a clear message instead of a stack trace
        st.error(f"Could not read the database: {exc}")
        st.stop()


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>', unsafe_allow_html=True
    )


def fmt_value(v: float, unit: str, kind: str) -> str:
    if pd.isna(v):
        return "n/a"
    a = abs(v)
    if unit in ("persons", "hectares") or unit.startswith("current US$") and kind == "level" and "person" not in unit:
        for div, suf in ((1e9, " B"), (1e6, " M")):
            if a >= div:
                return f"{v / div:,.2f}{suf}"
        return f"{v:,.0f}"
    if a >= 1000:
        return f"{v:,.0f}"
    return f"{v:,.1f}" if a >= 10 else f"{v:,.2f}"


def kpi_card(d: data_mod.Data, country: str, code: str, label: str | None = None) -> None:
    """Latest REPORTED value with its own reference year. Older than 2 years before the window end gets a badge."""
    lab = html.escape(label or d.name(code))
    latest = d.latest(country, code)
    ser = d.series(country, code).dropna()
    cov = f"{len(ser)} of {d.end - d.start + 1} years reported"
    if latest is None:
        st.markdown(
            f'<div class="kpi empty"><div class="lbl">{lab}</div><div class="val">No data</div>'
            f'<div class="meta"><span class="badge none">no observation for {html.escape(d.cname(country))}</span><br>'
            f"{cov}</div></div>",
            unsafe_allow_html=True,
        )
        return
    v, y = latest
    age = d.end - y
    badge = f'<span class="badge warn">last reported {y}: {age} yrs old</span>' if age > 2 else f'<span class="badge">{y}</span>'
    st.markdown(
        f'<div class="kpi"><div class="lbl">{lab}</div><div class="val">{fmt_value(v, d.unit(code), d.kind(code))}</div>'
        f'<div class="unit">{html.escape(d.unit(code))}</div>'
        f'<div class="meta">{badge} reference year {y}<br>{cov}<br>Source: World Bank WDI</div></div>',
        unsafe_allow_html=True,
    )


PRESETS = ["Selected ASEAN members", "Cambodia vs ASEAN (all 11)", "Cambodia vs Czechia", "All 12 countries", "Custom"]


def country_picker(d: data_mod.Data, key: str, container=None) -> list[str]:
    box = container or st
    preset = box.radio("Countries", PRESETS, key=f"{key}_preset")
    asean = compare.select_countries(d.countries, "asean")
    fmt = d.cname
    if preset == "Selected ASEAN members":
        sel = box.multiselect("ASEAN members", asean, default=["KHM", "THA", "VNM", "LAO"], format_func=fmt, key=f"{key}_asean")
    elif preset == "Cambodia vs ASEAN (all 11)":
        sel = asean
    elif preset == "Cambodia vs Czechia":
        sel = ["KHM", "CZE"]
    elif preset == "All 12 countries":
        sel = compare.select_countries(d.countries, "all")
    else:
        sel = box.multiselect("Any supported country", compare.select_countries(d.countries, "all"),
                              default=["KHM"], format_func=fmt, key=f"{key}_custom")
    if "CZE" in sel:
        box.caption("Czechia is an external benchmark, not an ASEAN member.")
    if not sel:
        box.warning("Select at least one country.")
    return sel


def csv_button(df: pd.DataFrame, filename: str, label: str = "Download CSV", key: str | None = None) -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv", key=key)


def source_box(d: data_mod.Data, code: str) -> None:
    r = d.ind(code)
    with st.expander("Source, definition and licence"):
        basis = (
            "stated in the official indicator name"
            if r.unit_basis == "name"
            else "inferred from the name and definition (the source publishes no unit string)"
        )
        st.markdown(f"**{r.indicator_name}** (`{code}`)  \nUnit: {r.unit} ({basis})")
        st.markdown(f"Source: {r.source_name}, World Bank. Original data: {r.source_organization or 'not stated'}")
        st.markdown(f"[Indicator page]({r.source_url}) · Retrieved {pd.Timestamp(r.retrieved_at):%Y-%m-%d}")
        st.markdown(f"Licence: {r.licence}")
        org = " ".join((r.source_organization or "not stated").split())
        st.markdown(f"Attribution: *The World Bank: World Development Indicators: {org}*")
        if r.notes:
            st.info(r.notes)
        st.markdown(f"Definition: {r.definition}")
