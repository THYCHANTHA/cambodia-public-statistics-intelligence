"""Read-only queries against the DuckDB store. NULL values are returned as NaN and never altered."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from cpsi.config import DB_PATH


def connect_ro(path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    if not Path(path).exists():
        raise FileNotFoundError(f"database not found: {path}. Run `python scripts/run_pipeline.py` first.")
    return duckdb.connect(str(path), read_only=True)


def countries(con) -> pd.DataFrame:
    return con.execute("SELECT * FROM countries ORDER BY country_group, country_name").df()


def indicators(con) -> pd.DataFrame:
    return con.execute("SELECT * FROM indicators ORDER BY domain, indicator_code").df()


def data_quality(con) -> pd.DataFrame:
    return con.execute("SELECT * FROM data_quality ORDER BY country_code, indicator_code").df()


def observations(
    con,
    indicator_codes: list[str] | None = None,
    country_codes: list[str] | None = None,
    start: int | None = None,
    end: int | None = None,
) -> pd.DataFrame:
    """Long table (one row per country-indicator-year, missing values included as NaN)."""
    where, params = [], []
    if indicator_codes:
        where.append(f"indicator_code IN ({','.join('?' * len(indicator_codes))})")
        params += list(indicator_codes)
    if country_codes:
        where.append(f"country_code IN ({','.join('?' * len(country_codes))})")
        params += list(country_codes)
    if start is not None:
        where.append("year >= ?")
        params.append(start)
    if end is not None:
        where.append("year <= ?")
        params.append(end)
    sql = (
        "SELECT country_code, indicator_code, year, value, unit, observation_status, source_name, retrieved_at "
        "FROM observations" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY 1, 2, 3"
    )
    return con.execute(sql, params).df()


def ingestion_summary(con) -> dict:
    row = con.execute(
        "SELECT count(*), count(value), min(retrieved_at), max(retrieved_at) FROM observations"
    ).fetchone()
    return {"rows": row[0], "reported": row[1], "first_retrieved": row[2], "last_retrieved": row[3]}
