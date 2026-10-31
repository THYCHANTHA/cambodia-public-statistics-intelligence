# Phase 2 findings: source validation (2026-10-31)

Machine-generated table: `source_validation.md` / `.json` (from `scripts/validate_sources.py`). This file is the human interpretation.

## World Bank Indicators API (primary source)
- Reachable, no key. All 12 countries (11 ASEAN + CZE) returned; ISO3 codes confirmed. The API names the Czech Republic "Czechia" and Viet Nam "Viet Nam".
- WDI source (id 2) last updated by the World Bank on 2026-10-08.
- **24 of 25 candidate codes validated as specified.**
- **1 substitution:** `EN.ATM.CO2E.PC` is archived (source "WDI Database Archives"; the data endpoint answers "The indicator was not found. It may have been deleted or archived"). Replaced by `EN.GHG.CO2.PC.CE.AR5` (EDGAR / JRC, CO2 excluding LULUCF, t CO2e per capita), 55 observations 1970-2024 for all 12 countries. The definition differs from the archived series, so values must not be compared with older publications of "CO2 per capita". Recorded in `configs/indicators.yaml`.
- Indicator **names differ slightly** from the brief for 12 codes (the API adds, for example, "(modeled ILO estimate)" or "total population"). The catalogue will store the API name as the authoritative name.
- Modelled estimates can be identified from the indicator name for: unemployment, employment in agriculture (modeled ILO estimate), maternal mortality (modeled estimate). Other series' modelled/direct status is not stated in the name and must be read from `sourceNote`; it will not be assumed.
- The API's `unit` field is empty for the indicators examined, so units will be taken from the indicator name and documented manually.

## Coverage gaps found (Cambodia, non-null observations in the 1960-2025 window)
Short or late series: literacy 10 (1998-2021), health expenditure 24 (2000-2023), secondary enrolment 21, electricity access 27, renewable energy 27 (to 2021), GDP series start 1975/76, inflation 31 (from 1995), exports/imports 33 (from 1993).
Country gaps: Myanmar has no exports/imports observations; Czechia has no adult literacy observations. All other country/indicator pairs have at least one observation. Observation counts for every country are in `source_validation.json`. These gaps will be shown, not filled.

## Licensing and terms (what was and was not verified)
- World Bank licence page (`datacatalog.worldbank.org/public-licenses`) answers HTTP 200 but is client-rendered: no licence text could be extracted by script. **CC BY 4.0 for WDI is not yet verified from the page** and must be read in a browser (or from the dataset's catalogue entry) before publication. Third-party exceptions per indicator are not exposed by the v2 API; `sourceOrganization` is recorded instead (e.g. EDGAR/JRC and IEA for the CO2 series).
- The WHO terms-of-use URL guessed from the brief returned 404; WHO terms are **not reviewed**.
- FAOSTAT: not touched (Project 01 already covers it).

## Optional sources
- **WHO GHO** (`ghoapi.azureedge.net`): HTTP 500 on every endpoint tried (indicator list, an indicator, dimension values), unfiltered and filtered, 2026-10-31. Cannot be validated now. Per the brief's fallback, WHO is deferred to `docs/NEXT_STEPS.md`; the World Bank health series are the working source.
- **ASEANstats** (`api.aseanstats.org`): HTTP 403 on the documentation page and on a data path, without a token. Consistent with the brief (token required). Not used; no attempt to bypass access.
- **UNData**: not tested (future enhancement per brief).

## Environment
Python 3.12.5; project venv `.venv` (system site-packages reused). DuckDB and Ruff were not installed system-wide; installation into the venv is recorded in the build status. D: free about 7.5 GB; this project is expected to stay well under 100 MB.
