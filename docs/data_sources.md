## Data sources and licences

| Source | Used? | Details |
|---|---|---|
| **World Bank, World Development Indicators (WDI)**, source id 2 | **Yes, the only source** | API `https://api.worldbank.org/v2/`; 25 indicators (see Indicator Explorer); 11 ASEAN members + Czechia; 1960-2025. WDI last updated by the World Bank 2026-10-08. |
| WHO Global Health Observatory | No | API returned HTTP 500 on 2026-10-31; terms not reviewed; deferred. |
| ASEANstats | No | Requires an approved token; not used, access restrictions not bypassed. |
| UNData (SDMX) | No | Future enhancement. |
| FAOSTAT | No | Project 01 already covers agricultural production. |

**Licence of the data.** World Bank Open Data is generally licensed CC BY 4.0, but individual series can carry third-party terms. Each indicator's original data provider is stored in the `indicators` table (`source_organization`). The CO2 series (`EN.GHG.CO2.PC.CE.AR5`) is compiled by EDGAR (JRC, European Commission) and IEA; CC BY 4.0 for it was reported from the World Bank indicator page by the project owner. The pipeline did not independently re-read these licence pages (they render only in a browser).

**Suggested attribution.** World Bank, World Development Indicators, retrieved via the World Bank Indicators API (https://api.worldbank.org/v2/); processed by Cambodia Public Statistics Intelligence (independent project). Original providers per indicator are listed in the Indicator Explorer.

**Code licence and data licence are separate.** The project code is MIT-licensed. The statistical data keep their own licences and are not re-licensed. The repository does not commit the cache, the DuckDB file or the Parquet export.
