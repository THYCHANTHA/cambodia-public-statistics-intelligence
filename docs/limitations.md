## Limitations

* **Single source.** All 24+1 indicators come from the World Bank's World Development Indicators. WHO, ASEANstats, UNData and FAOSTAT are not integrated (WHO's API returned HTTP 500 on 2026-10-31; ASEANstats requires a token; see `docs/NEXT_STEPS.md`). Findings are therefore as reliable as WDI and inherit its compilation choices and revisions.
* **Coverage is uneven and shown, not hidden.** About 30% of country-indicator-year cells are missing. Adult literacy has 99 reported values across 12 countries; Myanmar has no export/import values; Czechia has no adult literacy. Cambodia's literacy has 10 observations (1998-2021) and health expenditure 24 (2000-2023).
* **Modelled estimates.** Three series are labelled modelled in their official names. For the others the source name does not say whether values are direct reports, so none is called direct.
* **Units.** The API publishes no unit strings. Units were taken from the official indicator names (24 series) or inferred from name and definition (population, "persons"), and each is marked.
* **Suspicious source values.** Cambodia's GDP growth is exactly 0.0 in three years (1976, 1978, 1982) among non-zero values. This may indicate placeholders in the source; it was not verified against a primary source and the values are shown with a warning.
* **Nominal comparisons.** GDP, GDP per capita are in current US dollars: not inflation- or PPP-adjusted, and sensitive to exchange rates.
* **Revisions.** WDI values are revised. The data were retrieved on the date shown on the home page; a later refresh can change values.
* **Correlations** are exploratory, on non-independent country-year pairs, with no controls and no causal interpretation.
* **No regional aggregates** are shown; no provincial or sub-national data are included; no map.
* **Licences.** CC BY 4.0 (World Bank default) is applied because no indicator's metadata states otherwise; the CO2 series was individually verified by the owner. 18 series come from third-party international organisations whose own terms were not separately reviewed, which is why no data are redistributed in the repository. See `docs/data_sources.md`.
* This is not an official product of the Government of Cambodia, the National Institute of Statistics, the World Bank or ASEAN.
* **Responsive layout** was checked only at 500 px in headless Edge (not 390 px, not real devices), and only on desktop browsers' engine (Chromium/Edge). CSV download clicks were not exercised in a browser; the data behind each button are tested.
