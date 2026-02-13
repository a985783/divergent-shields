# 能源危机政策评估分析指南

## 项目概述

本项目评估2022年能源危机期间，西班牙"伊比利亚机制"与波兰货币政策在应对通胀冲击方面的效果差异。

### 核心研究问题
- 结构性市场干预（西班牙）vs. 传统货币政策（波兰）
- 供给冲击下的最优政策工具选择
- 汇率传导机制在危机中的作用

## 分析方法

### 1. 双重识别策略
- **西班牙**: 合成控制法（Synthetic Control Method, SCM）
- **波兰**: 局部投影（Local Projections, LP）

### 2. 数据要求
- 时间范围: 2019年1月 - 2023年12月
- 国家: 西班牙(ES)、波兰(PL) + 5个控制国
- 变量: 通胀指标、工业产出、能源价格、汇率

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
| `lp_enhanced_PL.csv` | 波兰局部投影结果 |
| `permutation_test_results.csv` | 置换检验结果 |
| `robustness_*.csv` | 稳健性检验结果 |
| `cost_benefit_sacrifice_ratio.csv` | 成本收益分析结果（区间估计） |
| `energy_structure_comparison.csv` | 能源结构对比数据 |

### 数据文档
- `data/DATA_SOURCES.md`: 详细数据来源与处理说明

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

## 联系方式

如有问题或建议：
- 创建GitHub Issue
- 邮件联系: qingsongcui9857@gmail.com

## 许可证

MIT License - 详见LICENSE文件
