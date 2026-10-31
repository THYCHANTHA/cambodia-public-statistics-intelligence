"""Plotly figures. Missing years break the line (no interpolation) and get their own visual treatment."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

NAVY, BLUE, GREY = "#0B1F3A", "#2F80C9", "#E5E7EB"
# Okabe-Ito colour-blind-safe set for comparison countries; Cambodia always uses the dark blue.
PALETTE = ["#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#7A6C00", "#8C564B", "#6B7280", "#000000"]
COUNTRY_COLOURS: dict[str, str] = {}


def colour(iso: str) -> str:
    if iso == "KHM":
        return "#1B4F9C"
    if iso not in COUNTRY_COLOURS:
        COUNTRY_COLOURS[iso] = PALETTE[len(COUNTRY_COLOURS) % len(PALETTE)]
    return COUNTRY_COLOURS[iso]


def _layout(fig: go.Figure, title: str, height: int = 430) -> go.Figure:
    fig.update_layout(
        title={"text": title, "font": {"size": 15, "color": NAVY}}, height=height, template="plotly_white",
        font={"color": NAVY}, margin={"l": 10, "r": 10, "t": 50, "b": 10}, hovermode="closest",
        legend={"orientation": "h", "y": -0.18}, transition={"duration": 300},
    )
    return fig


def trend_fig(df: pd.DataFrame, names: dict[str, str], ylabel: str, title: str, zero_line: bool = False) -> go.Figure:
    """df: country_code, year, y. NaN in y breaks the line, so gaps stay visible."""
    fig = go.Figure()
    for iso, g in df.groupby("country_code"):
        g = g.sort_values("year")
        fig.add_trace(go.Scatter(
            x=g["year"], y=g["y"], name=names.get(iso, iso), mode="lines+markers", connectgaps=False,
            line={"color": colour(iso), "width": 3.2 if iso == "KHM" else 1.8, "dash": "dash" if iso == "CZE" else "solid"},
            marker={"size": 5 if iso == "KHM" else 4},
            hovertemplate=f"{names.get(iso, iso)}<br>%{{x}}: %{{y:,.4g}}<extra></extra>",
        ))
    fig.update_yaxes(title=ylabel, zeroline=zero_line)
    fig.update_xaxes(title="Year", dtick=5)
    return _layout(fig, title)


def rank_fig(table: pd.DataFrame, unit: str, title: str) -> go.Figure:
    t = table[table["value"].notna()].sort_values("value")
    fig = go.Figure(go.Bar(
        x=t["value"], y=t["country_name"], orientation="h", text=[f"{v:,.4g}" for v in t["value"]], textposition="outside",
        marker={"color": [colour(c) for c in t["country_code"]]}, cliponaxis=False,
        hovertemplate="%{y}: %{x:,.4g}<extra></extra>",
    ))
    fig.update_xaxes(title=unit)
    return _layout(fig, title, height=max(260, 34 * len(t) + 110))


def coverage_fig(obs: pd.DataFrame, countries: list[str], names: dict[str, str], start: int, end: int,
                 title: str) -> go.Figure:
    """One row per country, one cell per year: blue = reported, grey = missing."""
    years = list(range(start, end + 1))
    rep = obs[obs.value.notna()].groupby("country_code")["year"].agg(set).to_dict()
    z = [[1 if y in rep.get(c, set()) else 0 for y in years] for c in countries]
    text = [[("reported" if v else "MISSING") for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        x=years, y=[names.get(c, c) for c in countries], z=z, text=text, zmin=0, zmax=1, showscale=False,
        colorscale=[[0, GREY], [0.5, GREY], [0.5, BLUE], [1, BLUE]], xgap=1, ygap=2,
        hovertemplate="%{y}, %{x}: %{text}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, title, height=max(200, 34 * len(countries) + 110))


def completeness_heatmap(cm: pd.DataFrame, names: dict[str, str], cnames: dict[str, str], title: str) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=cm.values, x=[c for c in cm.columns], y=[cnames.get(i, i) for i in cm.index], zmin=0, zmax=100,
        colorscale=[[0, GREY], [0.0001, "#DCEBF8"], [1, "#12457A"]], xgap=1, ygap=1,
        texttemplate="%{z:.0f}", textfont={"size": 9},
        customdata=[[names.get(c, c) for c in cm.columns]] * len(cm),
        hovertemplate="%{y}<br>%{customdata}<br>%{z:.1f}% of years reported<extra></extra>",
        colorbar={"title": "% years<br>reported"},
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickangle=-60)
    return _layout(fig, title, height=520)


def scatter_fig(df: pd.DataFrame, xlabel: str, ylabel: str, names: dict[str, str], title: str) -> go.Figure:
    fig = go.Figure()
    for iso, g in df.groupby("country_code"):
        fig.add_trace(go.Scatter(
            x=g["x"], y=g["y"], mode="markers", name=names.get(iso, iso), marker={"color": colour(iso), "size": 7, "opacity": 0.75},
            customdata=g["year"], hovertemplate=f"{names.get(iso, iso)} %{{customdata}}<br>x=%{{x:,.4g}}, y=%{{y:,.4g}}<extra></extra>",
        ))
    fig.update_xaxes(title=xlabel)
    fig.update_yaxes(title=ylabel)
    return _layout(fig, title)
