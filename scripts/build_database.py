"""Build the DuckDB store from cached World Bank responses (no network) and write the ingestion report."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cpsi.config import (  # noqa: E402
    CACHE_DIR,
    DB_PATH,
    END_YEAR,
    PROCESSED_DIR,
    REPORTS_DIR,
    START_YEAR,
    load_countries,
    load_indicators,
    load_units,
)
from cpsi.database import store  # noqa: E402
from cpsi.ingestion.world_bank import WorldBankClient  # noqa: E402
from cpsi.quality.completeness import completeness  # noqa: E402
from cpsi.transformation import observations as T  # noqa: E402


def build() -> dict:
    client = WorldBankClient(CACHE_DIR, offline=True)
    ccfg, icfg, units = load_countries(), load_indicators(), load_units()
    iso3 = [c["iso3"] for c in ccfg]

    cbundle = client.countries(iso3)
    countries = T.build_countries(client.records(cbundle), ccfg, cbundle["retrieved_at"])

    meta, frames, issues_by_code, log_rows = {}, [], {}, []
    log_rows.append(_log_row(client, "country", cbundle))
    for item in icfg:
        code = item["code"]
        mb = client.indicator_metadata(code)
        meta[code] = (client.records(mb)[0], mb["retrieved_at"])
        ob = client.observations(iso3, code, START_YEAR, END_YEAR)
        df, issues = T.parse_observations(
            client.records(ob), code, set(iso3), units[code]["unit"], ob["retrieved_at"], START_YEAR, END_YEAR
        )
        frames.append(df)
        issues_by_code[code] = issues
        log_rows += [_log_row(client, "meta", mb), _log_row(client, "obs", ob)]
    indicators = T.build_indicators(meta, icfg, units)
    obs = pd.concat(frames, ignore_index=True)

    bad = {c: i for c, i in issues_by_code.items() if T.count_issues(i)}
    if bad:
        raise T.ValidationError(f"validation issues, nothing loaded: {json.dumps(bad, default=str)[:800]}")

    retrieved = max(obs["retrieved_at"])
    dq = completeness(obs, iso3, indicators, START_YEAR, END_YEAR, retrieved)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    con = store.connect(DB_PATH)
    store.create_schema(con)
    store.load(con, "countries", countries)
    store.load(con, "indicators", indicators)
    store.load(con, "observations", obs)
    store.load(con, "data_quality", dq)
    store.load(con, "ingestion_log", pd.DataFrame(log_rows))

    obs.to_parquet(PROCESSED_DIR / "observations.parquet", index=False)
    return {"con": con, "issues": issues_by_code, "retrieved": retrieved}


def _log_row(client: WorldBankClient, _kind: str, bundle: dict) -> dict:
    path = client._cache_path(bundle["url"].removeprefix(client.base_url + "/"), bundle["params"])
    return {
        "request_url": bundle["url"],
        "request_params": json.dumps(bundle["params"], sort_keys=True),
        "retrieved_at": bundle["retrieved_at"],
        "pages": len(bundle["pages"]),
        "records": len(client.records(bundle)),
        "cache_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def q(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


def report(ctx: dict) -> None:
    con = ctx["con"]
    ncountry = q(con, "SELECT count(*) n FROM countries").n[0]
    nind = q(con, "SELECT count(*) n FROM indicators").n[0]
    expected = int(ncountry * nind * (END_YEAR - START_YEAR + 1))
    tot = q(con, """SELECT count(*) total, count(value) reported, count(*)-count(value) missing,
                    min(year) FILTER (WHERE value IS NOT NULL) first_y, max(year) FILTER (WHERE value IS NOT NULL) last_y,
                    count(*) FILTER (WHERE value = 0) zeros FROM observations""").iloc[0]
    by_c = q(con, """SELECT o.country_code, c.country_name, count(*) records, count(value) reported,
                     count(*)-count(value) missing, round(100.0*count(value)/count(*),1) pct_reported,
                     min(year) FILTER (WHERE value IS NOT NULL) first_year,
                     max(year) FILTER (WHERE value IS NOT NULL) latest_year
                     FROM observations o JOIN countries c ON c.iso3=o.country_code GROUP BY ALL ORDER BY o.country_code""")
    by_i = q(con, """SELECT indicator_code, count(*) records, count(value) reported, count(*)-count(value) missing,
                     round(100.0*count(value)/count(*),1) pct_reported,
                     min(year) FILTER (WHERE value IS NOT NULL) first_year,
                     max(year) FILTER (WHERE value IS NOT NULL) latest_year
                     FROM observations GROUP BY ALL ORDER BY indicator_code""")
    dup = q(con, """SELECT count(*) n FROM (SELECT 1 FROM observations GROUP BY source_name, country_code,
                    indicator_code, year HAVING count(*) > 1)""").n[0]
    zero_pairs = q(con, """SELECT d.country_code, d.indicator_code FROM data_quality d
                           WHERE valid_observations = 0 ORDER BY 1, 2""")
    focus = q(con, """SELECT country_code, indicator_code, valid_observations, first_year, latest_year,
                      internal_gap_years FROM data_quality WHERE
                      (country_code='MMR' AND indicator_code IN ('NE.EXP.GNFS.ZS','NE.IMP.GNFS.ZS')) OR
                      (country_code='KHM' AND indicator_code IN ('SE.ADT.LITR.ZS','SH.XPD.CHEX.GD.ZS'))
                      ORDER BY 1, 2""")
    warn = q(con, "SELECT country_code, indicator_code, validation_warnings FROM data_quality "
                  "WHERE validation_warnings IS NOT NULL AND valid_observations > 0 ORDER BY 1, 2")
    zeros = q(con, """SELECT indicator_code, country_code, count(*) n, min(year) first_year, max(year) last_year
                      FROM observations WHERE value = 0 GROUP BY ALL ORDER BY 1, 2""")
    grid = q(con, f"""SELECT count(*) n FROM (SELECT country_code, indicator_code FROM observations
                     GROUP BY ALL HAVING count(*) <> {END_YEAR - START_YEAR + 1})""").n[0]
    fk = {t: q(con, f"SELECT count(*) n FROM {t}").n[0] for t in store.TABLE_ORDER}

    result = {
        "retrieved_at_max": ctx["retrieved"],
        "window": [START_YEAR, END_YEAR],
        "expected_rows_full_grid": expected,
        "rows_loaded": int(tot.total),
        "reported_values": int(tot.reported),
        "missing_values": int(tot.missing),
        "missing_pct": round(100 * tot.missing / tot.total, 2),
        "zero_values": int(tot.zeros),
        "earliest_year_with_value": int(tot.first_y),
        "latest_year_with_value": int(tot.last_y),
        "duplicate_keys": int(dup),
        "country_indicator_pairs_without_full_year_grid": int(grid),
        "parse_issues": {c: T.count_issues(i) for c, i in ctx["issues"].items()},
        "table_row_counts": {k: int(v) for k, v in fk.items()},
        "pairs_with_zero_observations": zero_pairs.values.tolist(),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "ingestion_report.json").write_text(json.dumps(result, indent=1), encoding="utf-8")

    md = [
        "# Ingestion report (Phase 3)", "",
        f"Latest retrieval timestamp (UTC): {ctx['retrieved']}. Window {START_YEAR}-{END_YEAR}. "
        "Generated by `scripts/build_database.py` from the stored DuckDB tables.", "",
        "## Totals", "",
        f"- Rows retrieved and loaded: **{result['rows_loaded']:,}** (expected full grid {ncountry} countries x {nind} indicators x "
        f"{END_YEAR - START_YEAR + 1} years = {expected:,})",
        f"- Reported (non-null) values: **{result['reported_values']:,}**; missing (null in the source response): "
        f"**{result['missing_values']:,}** ({result['missing_pct']}%)",
        f"- Observed values equal to zero (kept as zero): {result['zero_values']}",
        f"- Earliest / latest year with a value: {result['earliest_year_with_value']} / {result['latest_year_with_value']}",
        "- Missing values are stored as NULL with status `missing`. The API does not distinguish 'not reported', "
        "'not available' and 'not applicable'; no such distinction is claimed.", "",
        "## Validation and duplicate checks", "",
        f"- Duplicate (source, country, indicator, year) keys: **{result['duplicate_keys']}**",
        f"- Country-indicator pairs without a complete year grid: **{result['country_indicator_pairs_without_full_year_grid']}**",
        f"- Parse issues (unknown country, indicator mismatch, bad year, non-numeric, out of window, duplicate): "
        f"**{sum(result['parse_issues'].values())}** across {len(result['parse_issues'])} indicators",
        f"- Table row counts: {result['table_row_counts']}",
        "- Primary keys, foreign keys and check constraints are enforced by DuckDB; the load would have failed otherwise.", "",
        "## Records by country", "", by_c.to_markdown(index=False), "",
        "## Records by indicator", "", by_i.to_markdown(index=False), "",
        "## Documented gaps requested for explicit record", "", focus.to_markdown(index=False), "",
        "## Observed zeros (kept as 0; not treated as missing)", "",
        "A zero can be genuine (e.g. internet use in 1990) or a source placeholder. Cambodia's GDP growth is exactly 0.0 "
        "in several late-1970s/early-1980s years, which is unusual and is reported as-is, not corrected.", "",
        zeros.to_markdown(index=False), "",
        f"## Country-indicator pairs with NO observation in the window ({len(zero_pairs)})", "",
        zero_pairs.to_markdown(index=False) if len(zero_pairs) else "None.", "",
        f"## Validation warnings on series that do have data ({len(warn)})", "",
        warn.to_markdown(index=False) if len(warn) else "None.", "",
    ]
    (REPORTS_DIR / "ingestion_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("parse_issues", "pairs_with_zero_observations")}, indent=1))
    print("pairs with zero observations:", result["pairs_with_zero_observations"])


if __name__ == "__main__":
    ctx = build()
    report(ctx)
    ctx["con"].close()
