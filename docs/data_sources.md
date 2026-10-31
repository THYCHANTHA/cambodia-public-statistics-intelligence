## Data sources and licences

| Source | Used? | Details |
|---|---|---|
| **World Bank, World Development Indicators (WDI)**, source id 2 | **Yes, the only source** | API `https://api.worldbank.org/v2/`; 25 indicators (see Indicator Explorer); 11 ASEAN members + Czechia; 1960-2025. WDI last updated by the World Bank 2026-10-08. |
| WHO Global Health Observatory | No | API returned HTTP 500 on 2026-10-31; terms not reviewed; deferred. |
| ASEANstats | No | Requires an approved token; not used, access restrictions not bypassed. |
| UNData (SDMX) | No | Future enhancement. |
| FAOSTAT | No | Project 01 already covers agricultural production. |

## Licence audit (2026-10-31)

**What the official terms say** (read on 2026-10-31):

* World Bank *Terms of Use for Datasets* (https://www.worldbank.org/ext/en/legal/terms-conditions/datasets; page dated 2018-03-23): unless labelled otherwise, datasets are provided under **CC BY 4.0**. Some datasets and indicators may not be redistributed or reused without the consent of the original data provider, or carry different terms; "where applicable, these conditions are included in the dataset or indicator metadata". The page names no specific providers.
* World Bank Data Catalog, *Data Access and Licensing* (https://datacatalog.worldbank.org/public-licenses): CC BY 4.0 is the default for datasets **produced by the World Bank itself**; many datasets are available under other labelled licences (ODbL, microdata research licence, licence specified externally, custom licence).

**What the indicator metadata says.** The API returns seven metadata fields per indicator (`id`, `name`, `source`, `sourceNote`, `sourceOrganization`, `topics`, `unit`). There is **no licence field**. A text search of `sourceNote` and `sourceOrganization` for all 25 indicators for *licence, creative commons, CC BY, copyright, restrict, permission, proprietary, terms* found **no match**. So no indicator states a different licence or a third-party restriction in the metadata the pipeline retrieved.

**Conclusion and its limits.**

* The World Bank default, CC BY 4.0, is applied to all 25 indicators, because nothing in their metadata says otherwise. The CO2 series `EN.GHG.CO2.PC.CE.AR5` was **individually verified as CC BY 4.0 by the project owner** on the World Bank indicator page; this pipeline did not itself read that page (it is client-rendered).
* **18 of the 25 series are named as compiled by international third-party organisations** (UN Population Division, IMF, ILO, FAO, UNESCO UIS, UNICEF/IGME, WHO, IEA, ITU, EDGAR/JRC; count made from the `sourceOrganization` text). The other 7 are national accounts (national statistical offices, central banks, OECD, World Bank staff estimates) and one World Bank ESMAP electrification series; those also rest on national and third-party inputs. See [indicator_sources.md](indicator_sources.md). The World Bank terms reserve the possibility of provider-specific terms; **those providers' own terms were not separately reviewed**.
* Mitigation: the repository does **not** redistribute any statistical data. The DuckDB store, Parquet export and raw API cache are git-ignored and are re-created from the public World Bank API by `python scripts/run_pipeline.py`. The repository contains only code, configuration, documentation and aggregate summary reports (counts and coverage statistics, plus the few observations quoted in the README and reports as findings, with attribution).

## Attribution

Format required by the World Bank terms: *The World Bank: Dataset name: Data source (if known)*. This project uses:

> The World Bank: World Development Indicators: *[original data source of the indicator, per [indicator_sources.md](indicator_sources.md)]*; retrieved via the World Bank Indicators API (https://api.worldbank.org/v2/) on 2026-10-31; processed by Cambodia Public Statistics Intelligence (independent project; changes: standardised units, derived growth/rolling statistics labelled as such).

The application prints this line per indicator in "Source, definition and licence". Original providers are in the `indicators` table (`source_organization`).

## Code licence and data licence are separate

The project **code** is MIT-licensed ([LICENSE](../LICENSE)). The statistical **data** keep their own licences and are not re-licensed under MIT.
