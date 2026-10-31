# Next steps (the deferred 20%)

Nothing below is implemented. Each item lists why it is useful, the data and libraries needed, the approach, dependencies, testing and research value.

## Data sources
**1. WHO Global Health Observatory.** *Why:* independent cross-check of life expectancy, mortality, health expenditure. *Data:* a few GHO indicators for 12 countries. *Libraries:* requests (existing client pattern). *Approach:* `who_gho.py` adapter writing the same long schema with its own `source_name`; the observation primary key already includes the source, so WHO and World Bank rows coexist without merging. *Dependencies:* on 2026-10-31 every GHO endpoint returned HTTP 500, and WHO terms of use were not reviewed (the URL tried returned 404). *Testing:* mocked responses, a definition-comparison table. *Value:* cross-source consistency analysis.

**2. ASEANstats (authorised).** *Why:* official regional statistics, which would replace any self-computed aggregate. *Data:* needs an approved bearer token (HTTP 403 without it on 2026-10-31). *Approach:* optional adapter reading `ASEANSTATS_TOKEN` from the environment; never committed; the core must keep working without it. *Testing:* mocked 401/403/200. *Value:* the only legitimate route to ASEAN-level aggregates.

**3. UNData / SDMX.** *Why:* indicators missing from WDI. *Libraries:* `sdmx1`. *Approach:* one targeted dataflow, not a general SDMX layer. *Value:* wider indicator coverage.

**4. More national statistics and FAOSTAT context.** *Why:* adult literacy (99 reported values across 12 countries) and health expenditure are sparse. *Approach:* national-source adapters with explicit definitions; do not duplicate Project 01's agricultural warehouse.

**5. Provincial Cambodian data and a map.** *Why:* the overview currently has no map. *Data:* provincial boundaries (e.g. geoBoundaries, as in Project 01) plus a provincial indicator source. *Libraries:* geopandas, plotly choropleth. *Dependencies:* a licensed provincial dataset.

## Analysis
**6. Clustering and PCA of socioeconomic indicators.** *Why:* group countries by development profile. *Data:* a complete country-year panel; missing values need an explicit, documented strategy (complete-case on a chosen year/indicator subset). *Libraries:* scikit-learn. *Testing:* stability across subsets; *Value:* multivariate view.

**7. Time-series forecasting and predictive development analytics.** *Why:* short-horizon outlook. *Libraries:* statsmodels. *Dependencies:* decide handling of structural breaks (e.g. 1970s). *Testing:* walk-forward evaluation against naive baselines. *Value:* honest forecast skill, with intervals.

**8. Advanced statistical modelling.** Panel regression with fixed effects; log-scale and detrended correlations; HAC or block-bootstrap intervals to replace the indicative p-values.

**9. Revision tracking.** Store each refresh as a dated vintage so WDI revisions are visible.

## Platform
**10. Warehouse integration with Project 01.** Load these tables into the PostgreSQL warehouse as a conformed dimension set.

**11. Role-based analytics.** Saved views and user roles, only if a multi-user deployment is needed.

**12. Public deployment and automated updates.** Streamlit Community Cloud or a container; a scheduled refresh in CI (needs the GitHub billing lock resolved) with a data-diff report and a licence re-check.

**13. Visual regression and accessibility testing** of the dashboard (screenshots are currently taken manually with headless Edge).
