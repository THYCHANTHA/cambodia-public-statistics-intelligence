# Phase 4: statistical analysis results

Computed by `scripts/phase4_report.py` from the existing DuckDB store (19,800 observation rows, 13,827 reported). No data were re-downloaded. Window 1960-2025. All analyses are exploratory and descriptive; none establishes causality.

## 1. Descriptive statistics: Cambodia, all 25 indicators

Computed on reported values only; `n` is the number of observations used.

| indicator_code       | indicator                                        |   n |   n_missing |   completeness_pct |       mean |     median |        min |        max |        std |   first_year |   latest_year |   latest_value |
|:---------------------|:-------------------------------------------------|----:|------------:|-------------------:|-----------:|-----------:|-----------:|-----------:|-----------:|-------------:|--------------:|---------------:|
| AG.LND.AGRI.ZS       | Agricultural land (% of land area)               |  64 |           2 |               97   |  24.3      |  25.6      |  13.9      |  34.7      |   6.92     |         1961 |          2024 |      34.7      |
| AG.LND.ARBL.HA       | Arable land (hectares)                           |  64 |           2 |               97   |   3.19e+06 |   3.7e+06  |   1.8e+06  |   4.12e+06 |   8e+05    |         1961 |          2024 |       4.12e+06 |
| EG.ELC.ACCS.ZS       | Access to electricity (% of population)          |  27 |          39 |               40.9 |  47.4      |  37.4      |   8.82     |  99.2      |  31.4      |         1998 |          2024 |      99.2      |
| EG.FEC.RNEW.ZS       | Renewable energy consumption (% of total final e |  27 |          39 |               40.9 |  70.4      |  74.1      |  51.4      |  82.5      |  11        |         1995 |          2021 |      52.4      |
| EN.GHG.CO2.PC.CE.AR5 | Carbon dioxide (CO2) emissions excluding LULUCF  |  55 |          11 |               83.3 |   0.279    |   0.154    |   0.0321   |   1.11     |   0.331    |         1970 |          2024 |       1.1      |
| FP.CPI.TOTL.ZG       | Inflation, consumer prices (annual %)            |  31 |          35 |               47   |   4.14     |   2.94     |  -1.24     |  24.1      |   4.96     |         1995 |          2025 |       2.35     |
| IT.NET.USER.ZS       | Individuals using the Internet (% of population) |  29 |          37 |               43.9 |  18.7      |   1.26     |   0        |  68.9      |  26.6      |         1990 |          2024 |      68.5      |
| NE.EXP.GNFS.ZS       | Exports of goods and services (% of GDP)         |  33 |          33 |               50   |  52.3      |  55.5      |  16.1      |  72.4      |  14.2      |         1993 |          2025 |      68.6      |
| NE.IMP.GNFS.ZS       | Imports of goods and services (% of GDP)         |  33 |          33 |               50   |  61.5      |  64.1      |  32.7      |  75.7      |  10.9      |         1993 |          2025 |      67.4      |
| NV.AGR.TOTL.ZS       | Agriculture, forestry, and fishing, value added  |  33 |          33 |               50   |  27.9      |  26.8      |  15.4      |  47.7      |  10.3      |         1993 |          2025 |      16.1      |
| NY.GDP.MKTP.CD       | GDP (current US$)                                |  51 |          15 |               77.3 |   1.19e+10 |   3.69e+09 |   7.16e+08 |   5.13e+10 |   1.45e+10 |         1975 |          2025 |       5.13e+10 |
| NY.GDP.MKTP.KD.ZG    | GDP growth (annual %)                            |  50 |          16 |               75.8 |   4.61     |   5.96     | -34.8      |  21.5      |   8.21     |         1976 |          2025 |       5.35     |
| NY.GDP.PCAP.CD       | GDP per capita (current US$)                     |  51 |          15 |               77.3 | 794        | 328        | 114        |   2.87e+03 | 811        |         1975 |          2025 |       2.87e+03 |
| SE.ADT.LITR.ZS       | Literacy rate, adult total (% of people ages 15  |  10 |          56 |               15.2 |  77.4      |  77.5      |  67.3      |  87.7      |   5.72     |         1998 |          2021 |      71.9      |
| SE.PRM.ENRR          | School enrollment, primary (% gross)             |  44 |          22 |               66.7 | 119        | 112        |  30.3      | 199        |  36        |         1971 |          2024 |     109        |
| SE.SEC.ENRR          | School enrollment, secondary (% gross)           |  21 |          45 |               31.8 |  36.4      |  39.1      |   9.24     |  58.8      |  16.6      |         1971 |          2024 |      58.8      |
| SH.DYN.MORT          | Mortality rate, under-5 (per 1,000 live births)  |  50 |          16 |               75.8 | 120        | 109        |  18.4      | 551        | 133        |         1975 |          2024 |      18.4      |
| SH.STA.MMRT          | Maternal mortality ratio (modeled estimate, per  |  39 |          27 |               59.1 | 413        | 344        | 137        | 874        | 235        |         1985 |          2023 |     137        |
| SH.XPD.CHEX.GD.ZS    | Current health expenditure (% of GDP)            |  24 |          42 |               36.4 |   5.47     |   5.49     |   4.27     |   6.92     |   0.88     |         2000 |          2023 |       4.62     |
| SL.AGR.EMPL.ZS       | Employment in agriculture (% of total employment |  35 |          31 |               53   |  56.8      |  58        |  33.4      |  77.7      |  15.8      |         1991 |          2025 |      33.4      |
| SL.UEM.TOTL.ZS       | Unemployment, total (% of total labor force) (mo |  35 |          31 |               53   |   0.643    |   0.716    |   0.119    |   1.26     |   0.314    |         1991 |          2025 |       0.263    |
| SP.DYN.LE00.IN       | Life expectancy at birth, total (years)          |  65 |           1 |               98.5 |  53.5      |  55.7      |  11.3      |  70.8      |  14.9      |         1960 |          2024 |      70.8      |
| SP.POP.GROW          | Population growth (annual %)                     |  65 |           1 |               98.5 |   1.83     |   1.56     |  -8.4      |   8.1      |   2.88     |         1961 |          2025 |       1.18     |
| SP.POP.TOTL          | Population, total                                |  66 |           0 |              100   |   1.02e+07 |   8.36e+06 |   5.09e+06 |   1.78e+07 |   4.37e+06 |         1960 |          2025 |       1.78e+07 |
| SP.URB.TOTL.IN.ZS    | Urban population (% of total population)         |  66 |           0 |              100   |  19.7      |  18        |   4.68     |  41.1      |   9.92     |         1960 |          2025 |      41.1      |

## 2. Trends: Cambodia, latest computable annual change and rolling means

A change is computed only when the immediately preceding calendar year is reported. Rolling means need all w consecutive years. Percent-valued series use percentage points, never percentage growth.

| indicator         |   latest_change_year | change_type              |   absolute_change |   pct_or_pp | rolling3_last    | rolling5_last    |
|:------------------|---------------------:|:-------------------------|------------------:|------------:|:-----------------|:-----------------|
| NY.GDP.PCAP.CD    |                 2025 | annual percentage growth |       244.5       |      9.306  | 2643 (2025)      | 2484 (2025)      |
| SP.POP.TOTL       |                 2025 | annual percentage growth |         2.092e+05 |      1.186  | 1.764e+07 (2025) | 1.742e+07 (2025) |
| SP.URB.TOTL.IN.ZS |                 2025 | percentage-point change  |         0.2329    |      0.2329 | 40.87 (2025)     | 40.62 (2025)     |
| IT.NET.USER.ZS    |                 2024 | percentage-point change  |        -0.4502    |     -0.4502 | 67.63 (2024)     | 64.01 (2024)     |
| SP.DYN.LE00.IN    |                 2024 | annual percentage growth |         0.149     |      0.2108 | 70.67 (2024)     | 70.27 (2024)     |

Cambodia GDP per capita: 51 reported years; years with a computable growth rate: 50; years inside the span without a value: 15.

## 3. Correlation (exploratory)

Exploratory only; correlation does not establish causality. p-values assume independent pairs, which country-year data are not (serial correlation within a country, shared trends), so treat them as indicative.

Pairs are country-years where both indicators are reported (pairwise deletion). Minimum 8 pairs. Raw (not log-transformed) values; Spearman is the safer summary for skewed variables such as GDP per capita.

| x                 | y              | sample              |   n_pairs |   pearson_r |   spearman_rho |   spearman_p | status   |
|:------------------|:---------------|:--------------------|----------:|------------:|---------------:|-------------:|:---------|
| NY.GDP.PCAP.CD    | SP.DYN.LE00.IN | pooled 12 countries |       644 |       0.529 |          0.9   |    9.67e-234 | ok       |
| NY.GDP.PCAP.CD    | SP.DYN.LE00.IN | Cambodia only       |        50 |       0.612 |          0.986 |    1.05e-38  | ok       |
| NY.GDP.PCAP.CD    | IT.NET.USER.ZS | pooled 12 countries |       360 |       0.582 |          0.724 |    9.79e-60  | ok       |
| NY.GDP.PCAP.CD    | IT.NET.USER.ZS | Cambodia only       |        29 |       0.916 |          0.992 |    1.53e-25  | ok       |
| NY.GDP.PCAP.CD    | SL.AGR.EMPL.ZS | pooled 12 countries |       420 |      -0.658 |         -0.922 |    1.91e-174 | ok       |
| NY.GDP.PCAP.CD    | SL.AGR.EMPL.ZS | Cambodia only       |        35 |      -0.957 |         -0.967 |    4.24e-21  | ok       |
| SP.URB.TOTL.IN.ZS | NY.GDP.PCAP.CD | pooled 12 countries |       656 |       0.636 |          0.839 |    2.69e-175 | ok       |
| SP.URB.TOTL.IN.ZS | NY.GDP.PCAP.CD | Cambodia only       |        51 |       0.956 |          0.988 |    8.65e-42  | ok       |
| NY.GDP.PCAP.CD    | SH.DYN.MORT    | pooled 12 countries |       636 |      -0.376 |         -0.928 |    8.66e-274 | ok       |
| NY.GDP.PCAP.CD    | SH.DYN.MORT    | Cambodia only       |        50 |      -0.521 |         -0.957 |    1.83e-27  | ok       |

## 4. Outlier flags (for review; no value is removed or changed)

Series tested (>= 8 reported values): 292. Rows flagged by either rule: 810; by both IQR (k=1.5) and robust z (|z|>3.5): 254.

Caveat: both rules treat a series as exchangeable values and ignore its time trend, so strongly trending or regime-changing series (population, GDP, land use) are flagged more often. A flag means 'look at this', not 'wrong'.

| indicator_code       |   flagged_rows |
|:---------------------|---------------:|
| AG.LND.AGRI.ZS       |             99 |
| AG.LND.ARBL.HA       |             55 |
| EG.ELC.ACCS.ZS       |             12 |
| EG.FEC.RNEW.ZS       |             21 |
| EN.GHG.CO2.PC.CE.AR5 |             46 |
| FP.CPI.TOTL.ZG       |             45 |
| IT.NET.USER.ZS       |             34 |
| NE.EXP.GNFS.ZS       |             14 |
| NE.IMP.GNFS.ZS       |             13 |
| NV.AGR.TOTL.ZS       |             37 |
| NY.GDP.MKTP.CD       |             93 |
| NY.GDP.MKTP.KD.ZG    |             42 |
| NY.GDP.PCAP.CD       |             65 |
| SE.ADT.LITR.ZS       |             10 |
| SE.PRM.ENRR          |             30 |
| SE.SEC.ENRR          |             12 |
| SH.DYN.MORT          |             47 |
| SH.STA.MMRT          |             11 |
| SH.XPD.CHEX.GD.ZS    |             17 |
| SL.AGR.EMPL.ZS       |              9 |
| SL.UEM.TOTL.ZS       |             37 |
| SP.DYN.LE00.IN       |              4 |
| SP.POP.GROW          |             26 |
| SP.POP.TOTL          |              7 |
| SP.URB.TOTL.IN.ZS    |             24 |

### Exact zeros in growth-rate series (review list)

| country_code   | indicator_code    |   year |   value | review_note                                                                                 |
|:---------------|:------------------|-------:|--------:|:--------------------------------------------------------------------------------------------|
| KHM            | NY.GDP.MKTP.KD.ZG |   1976 |    0.00 | exact zero in a growth-rate series: verify against the primary source; value left unchanged |
| KHM            | NY.GDP.MKTP.KD.ZG |   1978 |    0.00 | exact zero in a growth-rate series: verify against the primary source; value left unchanged |
| KHM            | NY.GDP.MKTP.KD.ZG |   1982 |    0.00 | exact zero in a growth-rate series: verify against the primary source; value left unchanged |
| THA            | FP.CPI.TOTL.ZG    |   1963 |    0.00 | exact zero in a growth-rate series: verify against the primary source; value left unchanged |

### Investigation: Cambodia GDP growth (NY.GDP.MKTP.KD.ZG), 1974-1985

|   year |     value | status     |
|-------:|----------:|:-----------|
|   1974 | nan       | MISSING    |
|   1975 | nan       | MISSING    |
|   1976 |   0       | EXACT ZERO |
|   1977 | -14.68    | reported   |
|   1978 |   0       | EXACT ZERO |
|   1979 | -12.83    | reported   |
|   1980 |  -5.668   | reported   |
|   1981 |   0.04109 | reported   |
|   1982 |   0       | EXACT ZERO |
|   1983 |   4.433   | reported   |
|   1984 |   4.932   | reported   |
|   1985 |   4.67    | reported   |

- Cambodia has exactly 3 zero values (1976, 1978, 1982), alternating with non-zero values in the same decade. Across all 12 countries and all years there are 3 exact zeros in this indicator, 3 of them Cambodian.
- An exact 0.0 for a continuously measured annual growth rate is unlikely in real data, especially between -14.7 and +0.04. This is a **pattern consistent with placeholder or imputed values in the source**, but this project cannot confirm that: the API provides no footnote (all footnotes are empty) and no primary-source check was done. Status: **flagged for review; values left unchanged; shown with a warning in the app.**

## 5. Country comparison

GDP per capita (current US$), ASEAN members, latest year in which all 11 have a value: **2025**. Rank among countries with a reported value in 2025 only; higher value = rank 1. Not a quality judgement. No ASEAN aggregate is computed.

|   rank | country_code   | country_name      |   year |    value | unit                   | status   | note   |
|-------:|:---------------|:------------------|-------:|---------:|:-----------------------|:---------|:-------|
|    1.0 | SGP            | Singapore         |   2025 | 98,814.0 | current US$ per person | reported |        |
|    2.0 | BRN            | Brunei Darussalam |   2025 | 32,234.6 | current US$ per person | reported |        |
|    3.0 | MYS            | Malaysia          |   2025 | 13,124.6 | current US$ per person | reported |        |
|    4.0 | THA            | Thailand          |   2025 |  8,056.6 | current US$ per person | reported |        |
|    5.0 | VNM            | Viet Nam          |   2025 |  5,066.0 | current US$ per person | reported |        |
|    6.0 | IDN            | Indonesia         |   2025 |  5,059.6 | current US$ per person | reported |        |
|    7.0 | PHL            | Philippines       |   2025 |  4,170.7 | current US$ per person | reported |        |
|    8.0 | KHM            | Cambodia          |   2025 |  2,872.4 | current US$ per person | reported |        |
|    9.0 | LAO            | Lao PDR           |   2025 |  2,324.8 | current US$ per person | reported |        |
|   10.0 | MMR            | Myanmar           |   2025 |  1,488.9 | current US$ per person | reported |        |
|   11.0 | TLS            | Timor-Leste       |   2025 |  1,341.0 | current US$ per person | reported |        |

Life expectancy, Cambodia vs Czechia, latest common year **2024**:

|   rank | country_code   |   year |   value | unit   |
|-------:|:---------------|-------:|--------:|:-------|
|   1.00 | CZE            |   2024 |   79.98 | years  |
|   2.00 | KHM            |   2024 |   70.82 | years  |

Latest year in which all 11 ASEAN members have adult literacy: None (None means no such year exists, so a strict same-year ranking is not possible and the app will say so).

## 6. Data-quality analysis

### Availability by country

| country_code   |   indicators_with_any_data |   indicators_with_recent_data |   indicators_total |
|:---------------|---------------------------:|------------------------------:|-------------------:|
| BRN            |                         25 |                            24 |                 25 |
| CZE            |                         24 |                            24 |                 25 |
| IDN            |                         25 |                            24 |                 25 |
| KHM            |                         25 |                            25 |                 25 |
| LAO            |                         25 |                            23 |                 25 |
| MMR            |                         23 |                            18 |                 25 |
| MYS            |                         25 |                            25 |                 25 |
| PHL            |                         25 |                            24 |                 25 |
| SGP            |                         25 |                            25 |                 25 |
| THA            |                         25 |                            25 |                 25 |
| TLS            |                         25 |                            24 |                 25 |
| VNM            |                         25 |                            25 |                 25 |

### Missing-year runs: Cambodia adult literacy and health expenditure

`SE.ADT.LITR.ZS`: {'n_reported': 10, 'completeness_pct': 15.15, 'first_year': 1998, 'latest_year': 2021, 'internal_gap_years': 14, 'stale': False, 'stale_reason': None}

|   first_missing_year |   last_missing_year |   length | type     |
|---------------------:|--------------------:|---------:|:---------|
|                 1960 |                1997 |       38 | leading  |
|                 1999 |                2003 |        5 | internal |
|                 2005 |                2007 |        3 | internal |
|                 2010 |                2012 |        3 | internal |
|                 2016 |                2018 |        3 | internal |
|                 2022 |                2025 |        4 | trailing |

`SH.XPD.CHEX.GD.ZS`: {'n_reported': 24, 'completeness_pct': 36.36, 'first_year': 2000, 'latest_year': 2023, 'internal_gap_years': 0, 'stale': False, 'stale_reason': None}

|   first_missing_year |   last_missing_year |   length | type     |
|---------------------:|--------------------:|---------:|:---------|
|                 1960 |                1999 |       40 | leading  |
|                 2024 |                2025 |        2 | trailing |

### Mean completeness by indicator across countries (percent of window years reported)

| indicator_code       |   mean_completeness_pct |
|:---------------------|------------------------:|
| AG.LND.AGRI.ZS       |                   93.00 |
| AG.LND.ARBL.HA       |                   93.00 |
| EG.ELC.ACCS.ZS       |                   45.20 |
| EG.FEC.RNEW.ZS       |                   46.60 |
| EN.GHG.CO2.PC.CE.AR5 |                   83.30 |
| FP.CPI.TOTL.ZG       |                   74.40 |
| IT.NET.USER.ZS       |                   45.50 |
| NE.EXP.GNFS.ZS       |                   66.00 |
| NE.IMP.GNFS.ZS       |                   66.00 |
| NV.AGR.TOTL.ZS       |                   69.80 |
| NY.GDP.MKTP.CD       |                   82.80 |
| NY.GDP.MKTP.KD.ZG    |                   81.20 |
| NY.GDP.PCAP.CD       |                   82.80 |
| SE.ADT.LITR.ZS       |                   12.50 |
| SE.PRM.ENRR          |                   62.70 |
| SE.SEC.ENRR          |                   53.20 |
| SH.DYN.MORT          |                   89.70 |
| SH.STA.MMRT          |                   59.10 |
| SH.XPD.CHEX.GD.ZS    |                   36.10 |
| SL.AGR.EMPL.ZS       |                   53.00 |
| SL.UEM.TOTL.ZS       |                   53.00 |
| SP.DYN.LE00.IN       |                   98.50 |
| SP.POP.GROW          |                   98.50 |
| SP.POP.TOTL          |                  100.00 |
| SP.URB.TOTL.IN.ZS    |                  100.00 |
