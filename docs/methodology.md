## Purpose

This observatory lets a reader explore how Cambodia's socioeconomic indicators have developed and how they compare with the other ASEAN members (and Czechia as an external benchmark) without downloading and aligning several datasets by hand. It is an independent educational and research project.

**Research question:** how can multi-source public statistical data integration and analytical visualisation improve access to information about Cambodia's socioeconomic development and its comparative position within Southeast Asia?

## Data flow

World Bank Indicators API (v2) -> raw JSON cache (`data/cache/`, with URL and retrieval timestamp) -> validation (country, indicator, year, numeric type, duplicates, record counts) -> standardised long table -> DuckDB (`countries`, `indicators`, `observations`, `data_quality`, `ingestion_log`) -> analysis functions -> this application. The application only reads DuckDB; it never calls an external API.

## Kinds of numbers you will see

| Kind | Meaning | Example |
|---|---|---|
| **Original observation** | A value published by the source, stored unchanged | GDP per capita 2024 |
| **Modelled estimate** | Published by the source but produced by a statistical model. Only flagged when the official indicator name says so | Unemployment (modeled ILO estimate); maternal mortality (modeled estimate) |
| **Derived value** | Computed here from observations, always labelled on screen | annual growth, percentage-point change, rolling mean |
| **Statistical calculation** | Summary of observations | mean, median, correlation |
| **Missing** | The source response contained no value (NULL). Stored as NULL, never as zero |  |

The source does not say whether a missing value was not collected, not available or not applicable, so this project does not claim that distinction. An observed **zero is a real value** and is kept as 0.

## Transformations

* **Absolute change** = value(t) - value(t-1), computed only when year t-1 has a reported value. Gaps are never bridged.
* **Annual percentage growth** = (value(t) / value(t-1) - 1) x 100, only for level and rate indicators, only when value(t-1) > 0 (no division by zero, no ratios over negative bases).
* **Percentage-point change** = value(t) - value(t-1) for indicators that are themselves percentages (shares, growth rates). It is a difference of two percentages and is **not** a percentage growth.
* **Rolling mean (3 or 5 years)** = mean of w consecutive calendar years ending at t; shown only if all w years are reported.
* Changes and rolling means are computed on the full series and then cut to the years you select, so the first displayed year can use the preceding year.
* **No interpolation, no forward fill, no imputation** anywhere.

## Statistics

* **Descriptive statistics** use reported observations only, inside the selected years. Every table shows n. Standard deviation is the sample SD (n-1) and is blank for n < 2.
* **Correlation** (Pearson, Spearman) uses country-year pairs where both indicators are reported (pairwise deletion); at least 8 pairs are required, otherwise no coefficient is shown. Pooled country-year data are not independent (trends within a country, shared global trends), so p-values are only indicative. Correlation is **exploratory and does not show causation.** Spearman is preferred for skewed variables such as GDP per capita.
* **Outlier flags** (IQR rule with k = 1.5; robust z-score 0.6745 x (x - median) / MAD with threshold 3.5) mark observations to look at. Both ignore time trends, so trending series are flagged more often. Flagged values are never removed or corrected.
* **Review flags**: an exact 0.0 in a continuous growth-rate series (growth, inflation) is flagged because it may be a placeholder in the source. Cambodia's GDP growth is exactly 0.0 in 1976, 1978 and 1982; this is reported, not corrected.

## Comparisons

A comparison uses one indicator and one reference year. Countries are ranked only among those with a reported value in that year; the others are listed as missing with their latest reported year. Rankings describe position on a number, not quality. **No ASEAN or regional aggregate is calculated**: an unweighted mean of country values is not an official regional statistic, and no authoritative aggregate has been loaded. Czechia is labelled an external benchmark. Timor-Leste joined ASEAN on 2025-10-26, so earlier values predate its membership.

## Definitions that matter

* The observation window is 1960-2025. A series' *completeness* is reported years divided by the 66 years of the window; *span completeness* divides by the years between its first and latest observation.
* A series is *stale* when its latest observation is more than 5 years before 2025. KPI cards always print the series' own reference year and warn when it is older than two years.
* **CO2 per capita** uses `EN.GHG.CO2.PC.CE.AR5` (EDGAR / JRC, CO2 excluding land use, land-use change and forestry, t CO2e per capita). It replaces the archived WDI series `EN.ATM.CO2E.PC`, which the API no longer serves. The definitions differ, so the two must not be joined into one historical series.
