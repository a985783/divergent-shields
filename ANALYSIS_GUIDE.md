# 能源危机政策评估分析指南

## 项目概述

本项目评估2022年能源危机期间，西班牙"伊比利亚机制"与波兰货币政策在应对通胀冲击方面的效果差异。

### 核心研究问题
- 结构性市场干预（西班牙）vs. 传统货币政策（波兰）
- 供给冲击下的最优政策工具选择
- 汇率传导机制在危机中的作用

## 分析方法

### 1. 双重识别策略
- **西班牙**：合成差分双重差分（SDID，Arkhangelsky et al., 2021）——统计推断采用时序安慰剂法
- **波兰**：状态依存局部投影（SD-LP，Auerbach & Gorodnichenko, 2012）——平滑转换函数区分危机与正常状态

### 2. 数据要求
- 时间范围：2019年1月 — 2023年12月
- 国家：西班牙（ES）、波兰（PL）+ 5个控制国（AT、DE、FR、IT、NL）
- 变量：HICP 通胀指标（headline、core、energy）、工业产出（IP_Total）、TTF 天然气价格、汇率

## 核心脚本

| 脚本 | 方法 | 输出 |
|------|------|------|
| `analysis/12_sdid_spain.py` | SDID + 时序安慰剂 | `sdid_results_ES*.csv`、`sdid_gap_ES_*.png` |
| `analysis/13_state_dependent_lp.py` | SD-LP 平滑转换 | `sdlp_PL_*.csv`、`sdlp_PL_*.png` |
| `analysis/10_fiscal_cost_estimation.py` | 牺牲率矩阵 | `sacrifice_ratio_matrix.csv` |
| `analysis/02_local_projections_enhanced.py` | LP（辅助） | `lp_enhanced_*.csv` |
| `analysis/03_synthetic_control_spain_enhanced.py` | SCM（辅助） | `scm_enhanced_ES_*.csv` |

## 输出文件

### 表格文件（`paper/tables/`）

| 文件 | 内容 |
|------|------|
| `sdid_results_ES.csv` | SDID 估计量汇总（含置信区间、安慰剂 p 值） |
| `sdid_results_ES_main.csv` | 主规格（不含葡萄牙） |
| `sdid_results_ES_with_PT.csv` | 稳健性规格（含葡萄牙） |
| `sdid_weights_ES_main.csv` | SDID 单位权重 |
| `sdlp_PL_crisis_vs_normal.csv` | SD-LP 危机 vs 正常状态系数（全部 horizon） |
| `sdlp_PL_summary.csv` | SD-LP h=6 和 h=12 摘要 |
| `sacrifice_ratio_matrix.csv` | 对称牺牲率矩阵（西班牙 vs 波兰） |
| `descriptive_stats.csv` | 描述性统计 |

### 图表文件（`paper/figures/`）

| 文件 | 内容 |
|------|------|
| `sdid_gap_ES_HICP_Total_main.png` | SDID gap 图（含 jackknife CI） |
| `sdlp_PL_HICP_Total_statedep.png` | SD-LP 双面板 IRF（危机 vs 正常） |
| `sdlp_PL_HICP_Core_statedep.png` | SD-LP 核心通胀 IRF |
| `sdlp_PL_IP_Total_statedep.png` | SD-LP 工业产出 IRF |

### 数据文档
- `data/DATA_SOURCES.md`：详细数据来源与处理说明

## 关键结果解读

### SDID 统计推断

- **时序安慰剂 p 值**：在前处理窗口内轮流设定虚假干预日期，计算经验 p 值；优于刀切法（小 N 时渐近正态假设不成立）
- **刀切 SE**：逐一剔除捐赠国得到的标准误，作为辅助诊断
- **单位权重**：各捐赠国对合成对照的贡献权重

### SD-LP 系数解读

- `beta_crisis_FX`（β^H）：高波动状态下 FX 冲击对通胀的影响
- `beta_normal_FX`（β^L）：低波动状态下 FX 冲击对通胀的影响
- 放大假说预测：β^H ≫ β^L，在 h=6—12 处统计显著

### 统计显著性标记

- `***`：p < 0.01
- `**`：p < 0.05
- `*`：p < 0.1

## 引用

```bibtex
@techreport{cui2026divergentshields,
  title={Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis},
  author={Cui, Qingsong},
  year={2026},
  note={Replication package: https://github.com/a985783/divergent-shields}
}
```

## 联系方式

- GitHub Issue 或邮件：qingsongcui9857@gmail.com
- 许可证：MIT（见 LICENSE）
