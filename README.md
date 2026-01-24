# Divergent Shields: Policy Evaluation Guide | 分歧的盾牌：政策评估指南

[English](#english) | [中文](#chinese)

---

<div id="english">

## Project Overview

This project evaluates the comparative effectiveness of Spain's "Iberian Mechanism" (structural market intervention) and Poland's independent monetary policy in response to the 2022 energy crisis inflation shock.

### Core Research Questions
- **Policy Choice**: Structural market intervention (Spain) vs. Traditional monetary policy (Poland)
- **Optimal Tools**: Selecting policy tools under supply-side shocks
- **Transmission**: The role of exchange rate channels during the crisis

## Methodology

### 1. Dual Identification Strategy
- **Spain**: Synthetic Control Method (SCM) - Estimating the counterfactual "no-intervention" scenario.
- **Poland**: Local Projections (LP) - Estimating the dynamic impulse response to monetary and energy shocks.

### 2. Data Requirements
- **Time Period**: Jan 2019 - Dec 2023
- **Countries**: Spain (ES), Poland (PL) + 5 Control countries
- **Variables**: Inflation indices (HICP), Industrial Production, Energy Prices, Exchange Rates

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the Analysis

```bash
# Option 1: Run all analyses (Recommended)
python run_all.py

# Option 2: Run main analyses only (Skip robustness checks, faster)
python run_all.py --fast

# Option 3: Step-by-step execution (Confirm each step)
python run_all.py --step
```

### Step-by-Step Execution

If you only want to run specific parts of the analysis:

```bash
# 1. Data Processing
python scripts/process_data.py

# 2. Descriptive Statistics
python analysis/01_descriptive.py

# 3. Local Projections (Enhanced)
python analysis/02_local_projections_enhanced.py

# 4. Synthetic Control Method (Enhanced)
python analysis/03_synthetic_control_spain_enhanced.py

# 5. Placebo Tests
python analysis/04_scm_placebo_tests.py

# 6. Robustness Checks (Optional)
python analysis/05_robustness_checks.py
```

## Output Files

### Tables (`paper/tables/`)

| File | Content |
|------|---------|
| `scm_diagnostics_summary.csv` | SCM model diagnostic statistics |
| `scm_enhanced_ES_*.csv` | Enhanced SCM results (3 variables) |
| `lp_enhanced_ES.csv` | Spain Local Projections results |
| `lp_enhanced_PL.csv` | Poland Local Projections results |
| `permutation_test_results.csv` | Permutation test results |
| `cost_benefit_sacrifice_ratio.csv` | Cost-benefit analysis results (Interval estimates) |

### Documentation
- `data/DATA_SOURCES.md`: Detailed data sources and processing instructions (Bilingual)

### Figures (`paper/figures/`)

| Pattern | Content |
|---------|---------|
| `scm_enhanced_*.png` | SCM results (with diagnostics) |
| `irf_enhanced_*.png` | Impulse Response Functions (with confidence bands) |
| `placebo_*.png` | Placebo tests |
| `robustness_*.png` | Robustness checks |

## Key Result Interpretation

### SCM Diagnostics
- **RMSPE**: Pre-treatment Root Mean Squared Prediction Error (Lower is better, <2 is good)
- **R²**: Goodness of fit (>0.8 is good)
- **Effective Donors**: Number of countries contributing to the synthetic counterfactual

### LP Significance
- `***`: p < 0.01 (Highly significant)
- `**`: p < 0.05 (Significant)
- `*`: p < 0.1 (Marginally significant)

## Technical Specifications

### Python Version
- **Required**: Python 3.8+
- **Tested**: Python 3.9.6

### Requirements
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Runtime**: 10-15 mins (Full), 5-8 mins (Fast)

## Citation

If you use this code, please cite:

```bibtex
@techreport{energyCrisisPolicy2026,
  title={Divergent Shields: A Comparative Assessment of the "Iberian Mechanism" and Monetary Independence during the 2022 Energy Crisis},
  author={Author Name},
  year={2026},
  institution={Institution},
  note={Python package available at: [repository URL]}
}
```

## License

MIT License - See [LICENSE](LICENSE) file.

</div>

---

<div id="chinese">

## 项目概述

本项目评估2022年能源危机期间，西班牙"伊比利亚机制"与波兰货币政策在应对通胀冲击方面的效果差异。

### 核心研究问题
- **政策选择**: 结构性市场干预（西班牙）vs. 传统货币政策（波兰）
- **最优工具**: 供给冲击下的最优政策工具选择
- **传导机制**: 汇率传导机制在危机中的作用

## 分析方法

### 1. 双重识别策略
- **西班牙**: 合成控制法（Synthetic Control Method, SCM）- 估计"无干预"反事实场景。
- **波兰**: 局部投影（Local Projections, LP）- 估计对货币和能源冲击的动态脉冲响应。

### 2. 数据要求
- **时间范围**: 2019年1月 - 2023年12月
- **国家**: 西班牙(ES)、波兰(PL) + 5个控制国
- **变量**: 通胀指标(HICP)、工业产出、能源价格、汇率

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行完整分析

```bash
# 方式1: 运行所有分析（推荐）
python run_all.py

# 方式2: 仅运行主要分析（跳过稳健性检验，更快）
python run_all.py --fast

# 方式3: 逐步运行（每步确认）
python run_all.py --step
```

### 分步运行

如果只想运行特定分析：

```bash
# 1. 数据处理
python scripts/process_data.py

# 2. 描述性统计
python analysis/01_descriptive.py

# 3. 局部投影（增强版）
python analysis/02_local_projections_enhanced.py

# 4. 合成控制法（增强版）
python analysis/03_synthetic_control_spain_enhanced.py

# 5. 安慰剂检验
python analysis/04_scm_placebo_tests.py

# 6. 稳健性检验（可选）
python analysis/05_robustness_checks.py
```

## 输出文件

### 表格文件 (`paper/tables/`)

| 文件 | 内容 |
|------|------|
| `scm_diagnostics_summary.csv` | SCM模型诊断统计量 |
| `scm_enhanced_ES_*.csv` | 增强SCM结果（3个变量） |
| `lp_enhanced_ES.csv` | 西班牙局部投影结果 |
| `lp_enhanced_PL.csv` | 波兰局部投影结果 |
| `permutation_test_results.csv` | 置换检验结果 |
| `cost_benefit_sacrifice_ratio.csv` | 成本收益分析结果（区间估计） |

### 数据文档
- `data/DATA_SOURCES.md`: 详细数据来源与处理说明 (双语版)

### 图表文件 (`paper/figures/`)

| 文件模式 | 内容 |
|----------|------|
| `scm_enhanced_*.png` | SCM结果图（含诊断） |
| `irf_enhanced_*.png` | 脉冲响应函数图（含置信带） |
| `placebo_*.png` | 安慰剂检验图 |
| `robustness_*.png` | 稳健性检验对比图 |

## 关键结果解读

### SCM诊断指标
- **RMSPE**: 预处理期均方根预测误差（越小越好，<2为良好）
- **R²**: 拟合优度（>0.8为良好）
- **Effective Donors**: 有效贡献国数量

### LP显著性标记
- `***`: p < 0.01（高度显著）
- `**`: p < 0.05（显著）
- `*`: p < 0.1（边缘显著）

## 技术说明

### Python版本
- **要求**: Python 3.8+
- **测试**: Python 3.9.6

### 运行要求
- **内存**: 最低 4GB RAM (推荐 8GB)
- **时间**: 10-15分钟 (完整), 5-8分钟 (快速)

## 引用

如果使用了本代码，请引用：

```bibtex
@techreport{energyCrisisPolicy2026,
  title={Divergent Shields: A Comparative Assessment of the "Iberian Mechanism" and Monetary Independence during the 2022 Energy Crisis},
  author={Author Name},
  year={2026},
  institution={Institution},
  note={Python package available at: [repository URL]}
}
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

</div>
