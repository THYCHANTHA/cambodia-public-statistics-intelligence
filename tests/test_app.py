"""Dashboard tests with Streamlit's headless AppTest against the real DuckDB store (skipped if it is not built)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cpsi.config import DB_PATH

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = ["Home.py", *sorted(p.name for p in (APP / "pages").glob("*.py"))]
pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="DuckDB store not built (run scripts/run_pipeline.py)")


def run(page: str) -> AppTest:
    path = APP / page if page == "Home.py" else APP / "pages" / page
    return AppTest.from_file(str(path), default_timeout=90).run()


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_without_exception(page):
    at = run(page)
    assert not at.exception, [e.value for e in at.exception]


def test_home_kpis_show_reference_year_and_source():
    at = run("Home.py")
    html = " ".join(m.value for m in at.markdown if "kpi" in m.value)
    assert html.count('class="kpi') == 8
    assert "reference year" in html and "Source: World Bank WDI" in html


def test_domain_page_filters_change_output():
    at = run("01_Economic_Development.py")
    assert not at.exception
    at.sidebar.radio(key="econ_mode").set_value("Year-to-year change").run()
    assert not at.exception
    at.sidebar.radio(key="econ_preset").set_value("Cambodia vs Czechia").run()
    assert not at.exception
    at.sidebar.selectbox(key="econ_ind").set_value("NY.GDP.MKTP.KD.ZG").run()
    assert not at.exception
    # the exact-zero review warning for Cambodia's GDP growth must be shown
    assert any("exact zero" in w.value for w in at.warning)


def test_percent_indicator_uses_percentage_points_label():
    at = run("02_Demographics.py")
    at.sidebar.selectbox(key="demo_ind").set_value("SP.URB.TOTL.IN.ZS").run()
    at.sidebar.radio(key="demo_mode").set_value("Year-to-year change").run()
    assert not at.exception
    assert any("Percentage-point change" in c.value for c in at.caption)


def test_asean_page_blocks_aggregates_and_handles_no_common_year():
    at = run("06_ASEAN_Comparison.py")
    assert any("No ASEAN or regional" in w.value for w in at.warning)
    at.sidebar.selectbox(key="cmp_ind").set_value("SE.ADT.LITR.ZS").run()
    at.sidebar.radio(key="cmp_preset").set_value("Cambodia vs ASEAN (all 11)").run()
    assert not at.exception
    assert any("no year in which every selected country" in i.value.lower() for i in at.info)


def test_explorer_search_filters_and_empty_state():
    at = run("07_Indicator_Explorer.py")
    at.text_input[0].set_value("mortality").run()
    assert not at.exception
    at.text_input[0].set_value("zzzz-no-such-indicator").run()
    assert not at.exception and any("No indicator matches" in w.value for w in at.warning)


def test_no_database_gives_clear_error_not_traceback(monkeypatch):
    import streamlit as st

    from cpsi.database import queries

    def boom(*a, **k):
        raise FileNotFoundError("database not found: test. Run `python scripts/run_pipeline.py` first.")

    st.cache_resource.clear()
    st.cache_data.clear()
    monkeypatch.setattr(queries, "connect_ro", boom)
    at = run("Home.py")
    assert not at.exception
    assert any("database not found" in e.value for e in at.error)
    st.cache_resource.clear()
    st.cache_data.clear()
