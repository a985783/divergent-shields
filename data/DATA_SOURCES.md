# Data Sources Documentation | 数据来源说明

[English](#english) | [中文](#chinese)

---

<div id="english">

## Overview
This document provides detailed information about all data sources used in the research project "Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis."

## 1. HICP (Harmonized Index of Consumer Prices)

**File**: `prc_hicp_midx.tsv.gz`  
**Source**: Eurostat  
**URL**: https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_midx/default/table  
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
3. Missing values: forward-filled for max 2 months

## 2. Industrial Production Index

**File**: `sts_inpr_m.tsv.gz`  
**Source**: Eurostat Short-Term Statistics  
**URL**: https://ec.europa.eu/eurostat/databrowser/view/sts_inpr_m  
**Time Coverage**: 2015-01 to 2023-12  

**Variables Used**:
- `IP_Total`: Total industrial production (index, 2015=100)
- Seasonally adjusted series

**Data Processing**:
1. Log-differenced to obtain growth rates
2. Used Eurozone aggregate (EA19) as control variable

## 3. Energy Prices

### 3.1 Brent Oil Price
**File**: `brent_oil_price_fred.csv`  
**Source**: FRED (Federal Reserve Economic Data)  
**Series ID**: DCOILBRENTEU  
**Frequency**: Daily (converted to monthly average)  
**Units**: USD per barrel (converted to EUR)

### 3.2 Natural Gas Price
**File**: `gas_price_imf.csv`  
**Source**: IMF Primary Commodity Prices  
**Series**: European Natural Gas (Dutch TTF)  
**Frequency**: Monthly  
**Units**: USD per mmbtu (converted to EUR/MWh)

## 4. Exchange Rates

### 4.1 PLN/EUR Exchange Rate
**File**: `ecb_pln_eur.csv`  
**Source**: ECB Statistical Data Warehouse  
**Series ID**: EXR.M.PLN.EUR.SP00.A  
**Frequency**: Monthly (end-of-month)  

### 4.2 USD/EUR Exchange Rate
**File**: `usd_eur_rate.csv`  
**Source**: FRED  
**Series ID**: DEXUSEU  

## 5. Data Quality and Limitations

### Missing Values
- HICP data: <1% missing, forward-filled (max 2 months)
- Industrial production: Complete for main countries
- Exchange rates: Complete

### Revisions
- All data downloaded in January 2024 reflect revisions through December 2023.

## Reproducibility
All data sources are publicly accessible. See `scripts/download_data.sh` for partial automation instructions.

</div>

---

<div id="chinese">

## 概述
本文档详细列出了研究项目"分歧的盾牌：2022年能源危机期间伊比利亚机制与货币独立性的比较评估"中使用的所有数据来源。

## 1. HICP (调和消费者物价指数)

**文件**: `prc_hicp_midx.tsv.gz`  
**来源**: Eurostat (欧盟统计局)  
**网址**: https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_midx/default/table  
**时间范围**: 2015年1月 - 2023年12月  
**覆盖范围**: 欧盟27国 + 其他欧洲国家  

**使用变量**:
- `HICP_Total`: 总体HICP指数 (COICOP: CP00)
- `HICP_Energy`: 能源分项 (CP045)
- `HICP_Core`: 核心通胀 (不含能源和未加工食品)
- `CP0451`: 电力价格 (具体子类)

**数据处理**:
1. 提取 ES, PL, DE, FR, IT, NL, AT 的数据
2. 将月度指数转换为同比年增长率
3. 缺失值处理: 向前填充 (最多2个月)

## 2. 工业生产指数 (Industrial Production Index)

**文件**: `sts_inpr_m.tsv.gz`  
**来源**: Eurostat 短期统计  
**网址**: https://ec.europa.eu/eurostat/databrowser/view/sts_inpr_m  
**时间范围**: 2015年1月 - 2023年12月  

**使用变量**:
- `IP_Total`: 工业生产总指数 (2015=100)
- 经季节性调整序列

**数据处理**:
1. 对数差分计算增长率
2. 使用欧元区聚合数据 (EA19) 作为控制变量

## 3. 能源价格

### 3.1 布伦特原油价格
**文件**: `brent_oil_price_fred.csv`  
**来源**: FRED (美联储经济数据)  
**系列ID**: DCOILBRENTEU  
**频率**: 日度 (转换为月度平均)  
**单位**: 美元/桶 (已转换为欧元)

### 3.2 天然气价格
**文件**: `gas_price_imf.csv`  
**来源**: IMF 初级商品价格  
**系列**: 欧洲天然气 (荷兰TTF)  
**频率**: 月度  
**单位**: 美元/mmbtu (已转换为欧元/MWh)

## 4. 汇率数据

### 4.1 波兰兹罗提/欧元 (PLN/EUR)
**文件**: `ecb_pln_eur.csv`  
**来源**: ECB (欧洲央行) 统计数据仓库  
**系列ID**: EXR.M.PLN.EUR.SP00.A  
**频率**: 月度 (月末值)  

### 4.2 美元/欧元 (USD/EUR)
**文件**: `usd_eur_rate.csv`  
**来源**: FRED  
**系列ID**: DEXUSEU  
**用途**: 用于将美元计价的能源价格转换为欧元

## 5. 数据质量与限制

### 缺失值
- HICP数据: 缺失<1%，采用向前填充 (max 2个月)
- 工业生产: 主要国家数据完整
- 汇率: 完整无缺失

### 数据修订
- 所有数据下载于2024年1月，反映了截至2023年12月的数据修订情况。

## 可复现性
所有数据来源均为公开可获取。自动化下载脚本见 `scripts/download_data.sh`。

</div>
