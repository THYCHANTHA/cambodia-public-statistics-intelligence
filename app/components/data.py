"""Cached, read-only access to the DuckDB store for the Streamlit app. Nothing here calls an external API."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from cpsi.config import END_YEAR, START_YEAR
from cpsi.database import queries


@st.cache_resource(show_spinner="Opening database...")
def _connection():
    return queries.connect_ro()


@st.cache_data(show_spinner="Loading data from DuckDB...")
def _load() -> dict:
    con = _connection()
    return {
        "countries": queries.countries(con),
        "indicators": queries.indicators(con),
        "dq": queries.data_quality(con),
        "obs": queries.observations(con),
        "summary": queries.ingestion_summary(con),
    }


class Data:
    """Thin wrapper with lookups. All frames are the cached originals: treat them as read-only."""

    def __init__(self, raw: dict):
        self.countries: pd.DataFrame = raw["countries"]
        self.indicators: pd.DataFrame = raw["indicators"]
        self.dq: pd.DataFrame = raw["dq"]
        self.obs: pd.DataFrame = raw["obs"]
        self.summary: dict = raw["summary"]
        self.start, self.end = START_YEAR, END_YEAR
        self._ind = self.indicators.set_index("indicator_code")
        self._cty = self.countries.set_index("iso3")

    # lookups
    def cname(self, iso: str) -> str:
        return self._cty.loc[iso, "country_name"]

    def ind(self, code: str) -> pd.Series:
        return self._ind.loc[code]

    def name(self, code: str) -> str:
        return self._ind.loc[code, "indicator_name"]

    def unit(self, code: str) -> str:
        return self._ind.loc[code, "unit"]

    def kind(self, code: str) -> str:
        return self._ind.loc[code, "value_kind"]

    def series(self, country: str, code: str) -> pd.Series:
        g = self.obs[(self.obs.country_code == country) & (self.obs.indicator_code == code)]
        return g.set_index("year")["value"].sort_index()

    def latest(self, country: str, code: str) -> tuple[float, int] | None:
        s = self.series(country, code).dropna()
        return (float(s.iloc[-1]), int(s.index[-1])) if len(s) else None

    def slice(self, codes: list[str], countries: list[str], start: int, end: int) -> pd.DataFrame:
        o = self.obs
        return o[o.indicator_code.isin(codes) & o.country_code.isin(countries) & o.year.between(start, end)]


def load() -> Data:
    return Data(_load())
