"""DuckDB analytical store: schema with enforced keys, and loaders."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

DDL = """
CREATE TABLE countries (
    iso3 VARCHAR PRIMARY KEY,
    country_name VARCHAR NOT NULL,
    iso2 VARCHAR,
    world_bank_code VARCHAR NOT NULL,
    region VARCHAR,
    income_level VARCHAR,
    capital_city VARCHAR,
    country_group VARCHAR NOT NULL CHECK (country_group IN ('ASEAN', 'EXTERNAL_BENCHMARK')),
    asean_member_since DATE,
    source VARCHAR NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE indicators (
    indicator_code VARCHAR PRIMARY KEY,
    indicator_name VARCHAR NOT NULL,
    domain VARCHAR NOT NULL,
    unit VARCHAR NOT NULL,
    unit_basis VARCHAR NOT NULL CHECK (unit_basis IN ('name', 'inferred')),
    value_kind VARCHAR NOT NULL,
    estimate_type VARCHAR,
    replaces_code VARCHAR,
    definition VARCHAR,
    source_name VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    source_organization VARCHAR,
    frequency VARCHAR NOT NULL,
    notes VARCHAR,
    licence VARCHAR NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE observations (
    country_code VARCHAR NOT NULL REFERENCES countries (iso3),
    indicator_code VARCHAR NOT NULL REFERENCES indicators (indicator_code),
    year INTEGER NOT NULL CHECK (year BETWEEN 1900 AND 2100),
    value DOUBLE,
    unit VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    footnote VARCHAR,
    observation_status VARCHAR NOT NULL CHECK (observation_status IN ('reported', 'missing')),
    retrieved_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (source_name, country_code, indicator_code, year),
    CHECK ((observation_status = 'missing') = (value IS NULL))
);
CREATE TABLE data_quality (
    country_code VARCHAR NOT NULL REFERENCES countries (iso3),
    indicator_code VARCHAR NOT NULL REFERENCES indicators (indicator_code),
    window_start INTEGER NOT NULL,
    window_end INTEGER NOT NULL,
    window_years INTEGER NOT NULL,
    valid_observations INTEGER NOT NULL,
    missing_observations INTEGER NOT NULL,
    first_year INTEGER,
    latest_year INTEGER,
    completeness_pct DOUBLE NOT NULL,
    span_completeness_pct DOUBLE,
    internal_gap_years INTEGER NOT NULL,
    validation_warnings VARCHAR,
    retrieved_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (country_code, indicator_code)
);
CREATE TABLE ingestion_log (
    request_url VARCHAR NOT NULL,
    request_params VARCHAR NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    pages INTEGER NOT NULL,
    records INTEGER NOT NULL,
    cache_sha256 VARCHAR NOT NULL,
    PRIMARY KEY (request_url, request_params, retrieved_at)
);
"""

TABLE_ORDER = ["countries", "indicators", "observations", "data_quality", "ingestion_log"]


def connect(path: Path, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only)


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    for name in reversed(TABLE_ORDER):
        con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute(DDL)


def load(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    """Insert a frame by column name (order-independent). NaN values become NULL."""
    cols = ", ".join(df.columns)
    frame = df.astype(object).where(df.notna(), None)
    con.register("_incoming", frame)
    try:
        con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM _incoming")
    finally:
        con.unregister("_incoming")
    return len(df)
