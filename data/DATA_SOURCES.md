# Data Sources Documentation

## Overview
This document provides detailed information about all data sources used in the research project "Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis."

---

##  1. HICP (Harmonized Index of Consumer Prices)

**File**: `prc_hicp_midx.tsv.gz`  
**Source**: Eurostat  
**URL**: https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_midx/default/table  
**Download Date**: 2024-01-15  
**Data Version**: Last updated 2024-01-10  
**Time Coverage**: 2015-01 to 2023-12  
**Geographic Coverage**: EU27 + additional European countries  

**Variables Used**:
- `HICP_Total`: Overall HICP index (COICOP: CP00)
- `HICP_Energy`: Energy component (CP045)
- `HICP_Core`: Core inflation (excl. energy and unprocessed food)
- `CP0451`: Electricity prices (specific subcategory)

**Data Processing**:
1. Extracted data for ES, PL, DE, FR, IT, NL, AT
2. Converted monthly index to year-over-year growth rates
3. Handled missing values: forward-filled for max 2 months

---

## 2. Industrial Production Index

**File**: `sts_inpr_m.tsv.gz`  
**Source**: Eurostat Short-Term Statistics  
**URL**: https://ec.europa.eu/eurostat/databrowser/view/sts_inpr_m  
**Download Date**: 2024-01-15  
**Data Version**: Last updated 2024-01-08  
**Time Coverage**: 2015-01 to 2023-12  

**Variables Used**:
- `IP_Total`: Total industrial production (index, 2015=100)
- Seasonally adjusted series

**Data Processing**:
1. Log-differenced to obtain growth rates
2. Used Eurozone aggregate (EA19) as control variable

---

## 3. Energy Prices

### 3.1 Brent Oil Price

**File**: `brent_oil_price_fred.csv`  
**Source**: Federal Reserve Economic Data (FRED)  
**Series ID**: DCOILBRENTEU  
**URL**: https://fred.stlouisfed.org/series/DCOILBRENTEU  
**Download Date**: 2024-01-12  
**Frequency**: Daily (converted to monthly average)  
**Units**: USD per barrel  

**Data Processing**:
1. Averaged daily prices to monthly
2. Converted to EUR using USD/EUR exchange rate
3. Log-differenced for shock identification

### 3.2 Natural Gas Price

**File**: `gas_price_imf.csv`  
**Source**: International Monetary Fund (IMF) Primary Commodity Prices  
**Series**: European Natural Gas (Dutch TTF)  
**URL**: https://www.imf.org/en/Research/commodity-prices  
**Download Date**: 2024-01-12  
**Frequency**: Monthly  
**Units**: USD per mmbtu (converted to EUR/MWh)  

**Data Processing**:
1. Converted from USD/mmbtu to EUR/MWh
2. Log-differenced: `DL_Gas_EUR = 100 * log(Gas_t / Gas_{t-1})`

---

## 4. Exchange Rates

### 4.1 PLN/EUR Exchange Rate

**File**: `ecb_pln_eur.csv`  
**Source**: European Central Bank Statistical Data Warehouse  
**Series ID**: EXR.M.PLN.EUR.SP00.A  
**URL**: https://sdw.ecb.europa.eu/  
**Download Date**: 2024-01-12  
**Frequency**: Monthly (end-of-month)  

**Data Processing**:
1. Log-differenced: `DL_XR_Local = 100 * log(XR_t / XR_{t-1})`
2. Positive values = PLN depreciation

### 4.2 USD/EUR Exchange Rate

**File**: `usd_eur_rate.csv`  
**Source**: FRED  
**Series ID**: DEXUSEU  
**Download Date**: 2024-01-12  

**Usage**: Used for converting USD-denominated prices to EUR

---

## 5. Energy Structure Data (Reference)

**Source**: International Energy Agency (IEA) - Electricity Information 2022  
**URL**: https://www.iea.org/data-and-statistics  
**Access Date**: 2024-01-10  
**Usage**: Validation of donor pool selection (Spain-Italy energy mix similarity)

**Key Statistics (2021)**:
- Spain: Gas-fired generation ~48%, Renewables ~30%, Nuclear ~22%
- Italy: Gas-fired generation ~45%, Renewables ~35%, Other ~20%
- Germany: Coal ~30%, Renewables ~40%, Gas ~15%, Nuclear ~12%
- France: Nuclear ~70%, Renewables ~20%, Gas ~7%

---

## Data Quality and Limitations

### Missing Values
- HICP data: \u003c1% missing, forward-filled (max 2 months)
- Industrial production: Complete for main countries
- Exchange rates: Complete (no missing)

### Revisions
- Eurostat data subject to revisions up to 3 months after initial release
- All data downloaded in January 2024 reflect revisions through December 2023

### Frequency Alignment
- All series converted to monthly frequency
- Daily data (oil prices, exchange rates) averaged to month-end values

---

## Reproducibility

### Data Access
All data sources are publicly accessible and free of charge (registration may be required for some Eurostat bulk downloads).

### Code for Data Download
See `scripts/download_data.sh` for automated download scripts (requires API keys for some sources).

### Data Processing Pipeline
```
raw/ → scripts/process_data.py → processed/merged_data.csv
```

Full processing code available in:
- `scripts/process_data.py`: Main processing script
- `scripts/utils.py`: Helper functions for data cleaning

---

## Contact for Data Issues

If you encounter issues reproducing the data:
1. Check data source URLs (may have changed)
2. Verify download dates (historical data may be updated)
3. Contact: [author email] for processed data availability

---

**Last Updated**: 2024-01-24  
**Document Version**: 1.0
