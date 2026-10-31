# data/

Everything in this folder is **generated** and git-ignored; run `python scripts/run_pipeline.py` to create it.

* `cache/`: raw World Bank API response bundles (URL, parameters, retrieval time, all pages).
* `processed/`: `cpsi.duckdb` (analytical store) and `observations.parquet`.

The statistical data are World Bank World Development Indicators and keep their own licences (see `docs/data_sources.md`). They are not committed because of that and because they are reproducible from the API.
