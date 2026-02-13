# 分歧的盾牌：2022年能源危机期间"伊比利亚机制"与货币政策独立性的比较评估

语言 / Language: 中文（当前） | [English](README_EN.md)

## 项目概述

### 研究背景
2022年能源危机构成了欧洲自1970年代以来最严重的能源价格冲击。天然气价格飙升超过10倍，对欧洲经济体造成了残酷的贸易条件冲击。然而，冲击向国内消费者价格的传导并不均匀，而是由不同的国家政策框架调节。

### 研究问题
本项目利用西班牙和波兰在危机期间的不同反应所创造的自然实验，探讨了一个根本性问题：**面对极端的、缺乏弹性的供应冲击，结构性市场干预是否优于货币正统政策？**

### 主要发现
1. **西班牙的结构性盾牌**：使用合成控制法（SCM）构建了一个"无所作为的西班牙"的反事实情景，发现伊比利亚机制使西班牙避免了额外约3个百分点的 headline 通胀。
2. **波兰的货币惩罚**：使用局部投影（LP）方法分离了汇率的作用，发现波兰的货币独立性成为了一种负担；兹罗提（PLN）的贬值对进口能源通胀起到了放大作用。

## 项目结构

```
分歧的盾牌-完结_存档/
├── analysis/              # 分析脚本（Python）
├── data/                  # 数据文件
│   ├── raw/              # 原始数据文件
│   └── processed/        # 处理后的数据文件
├── paper/                # 论文相关文件
│   ├── figures/          # 图表文件
│   ├── tables/           # 表格文件
│   └── paper.md          # 论文内容（Markdown）
├── scripts/              # 数据处理脚本
├── run_all.py            # 主运行脚本
├── requirements.txt      # Python依赖
├── ANALYSIS_GUIDE.md     # 分析指南
└── README.md             # 项目说明（本文档）
```

## 快速开始指南

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键执行与验证（推荐用于复现包）

```bash
# 快速复现主结果
python run_all.py --fast

# 复现完整流程（含稳健性）
python run_all.py

# 产物完整性检查
python scripts/verify_reproducibility.py
```

详细可复现性流程见英文版 `REPRODUCIBILITY.md` 与中文版 `REPRODUCIBILITY_ZH.md`。

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

# 7. 共形推断
python analysis/06_scm_conformal_inference.py

# 8. 敏感性分析
python analysis/07_donor_sensitivity_analysis.py

# 9. 平行趋势检验
python analysis/08_pretrend_tests.py

# 10. 内生性检验
python analysis/09_timing_robustness.py

# 11. 财政成本估算
python analysis/10_fiscal_cost_estimation.py
```

## 数据来源和处理说明

### 数据来源
- **Eurostat**：HICP（调和消费者价格指数）组成部分、工业生产指数
- **FRED**：布伦特原油价格、汇率数据
- **IEA**：能源依赖指标
- **National Statistical Agencies**：西班牙INE、波兰GUS

### 数据处理
数据处理脚本 `scripts/process_data.py` 负责：
1. 读取和清理Eurostat的TSV格式数据
2. 合并多个数据源
3. 计算同比增长率
4. 处理缺失值和异常值
5. 生成最终的合并数据集 `merged_data.csv`

### 数据文件
- `data/raw/prc_hicp_midx.tsv.gz`：HICP数据（压缩TSV格式）
- `data/processed/merged_data.csv`：处理后的合并数据集（CSV格式）

## 分析方法介绍

### 1. 合成控制法（SCM）- 西班牙分析

#### 方法概述
合成控制法由Abadie等人（2010）开发，用于评估案例研究政策干预的效果。通过构建一个"合成"的反事实单位（加权平均的控制组），来估计如果没有实施政策，结果变量的可能路径。

#### 实施细节
- **供体池**：奥地利（AT）、德国（DE）、法国（FR）、意大利（IT）、荷兰（NL）
- **预测变量**：干预前的通胀趋势、工业生产、能源依赖指标
- **优化目标**：最小化干预前的均方根预测误差（RMSPE）

#### 关键诊断指标
- **RMSPE**：预处理期均方根预测误差（越小越好，<2为良好）
- **R²**：拟合优度（>0.8为良好）
- **Effective Donors**：有效贡献国数量

#### 代码位置
```bash
python analysis/03_synthetic_control_spain_enhanced.py
```

### 2. 局部投影（LP）- 波兰分析

#### 方法概述
局部投影由Jordà（2005）提出，用于估计冲击对结果变量的脉冲响应函数（IRF）。该方法直接在每个预测时域上估计回归模型，提供了一种灵活的替代VAR模型的方法。

#### 实施细节
- **规格**：分解通胀响应为全球成分和国内货币成分
- **冲击变量**：
  - 全球冲击：以欧元计价的TTF天然气价格变动
  - 汇率冲击：波兰兹罗提（PLN）对欧元的汇率变动
- **交互项**：添加了 `Gas × FX` 交互项，以证实"双重打击"假设

#### 关键结果
- 货币贬值在12个月 horizon 内每1%贬值会使核心通胀增加0.312个百分点（p<0.05）
- 汇率成分占危机高峰期核心通胀差异的近50%

#### 代码位置
```bash
python analysis/02_local_projections_enhanced.py
```

## 结果解释

### 主要结果

#### 西班牙 - 伊比利亚机制的效果
- 使用增强型合成控制法估计，伊比利亚机制使 headline 通胀相对于其合成同行组降低了**1.74个百分点**（同比）
- 模型实现了出色的干预前拟合（R²=0.88，RMSPE=1.19）
- 有效抑制了电力价格对全球天然气价格的传导

#### 波兰 - 汇率传导机制
- 确定了"顺周期汇率成分"
- 汇率贬值在12个月 horizon 内每1%贬值会使核心通胀增加0.312个百分点（p<0.05）
- 汇率成分占危机高峰期核心通胀差异的近50%

### 财政成本分析
估算伊比利亚机制的财政成本约为51亿欧元，效费比优于货币紧缩政策。

### 稳健性检验
- **安慰剂检验**：空间和时间安慰剂检验
- **Donor敏感性分析**：Leave-One-Out分析，论证了意大利的关键性
- **平行趋势检验**：p=0.12，支持平行趋势假设
- **共形推断**：提供了非渐近预测区间

## 代码结构说明

### 分析脚本

| 文件 | 功能 | 描述 |
|------|------|------|
| `01_descriptive.py` | 描述性分析 | 生成基本统计量和时间序列图 |
| `02_local_projections_enhanced.py` | 局部投影（增强版） | 波兰汇率传导分析 |
| `03_synthetic_control_spain_enhanced.py` | 合成控制法（增强版） | 西班牙伊比利亚机制效果分析 |
| `04_scm_placebo_tests.py` | 安慰剂检验 | 空间和时间安慰剂检验 |
| `05_robustness_checks.py` | 稳健性检验 | 不同控制组和时间窗口的检验 |
| `06_scm_conformal_inference.py` | 共形推断 | 提供统计推断的置信区间 |
| `07_donor_sensitivity_analysis.py` | 敏感性分析 | Donor池敏感性分析 |
| `08_pretrend_tests.py` | 平行趋势检验 | 检验平行趋势假设 |
| `09_timing_robustness.py` | 内生性检验 | 多时点安慰剂检验 |
| `10_fiscal_cost_estimation.py` | 财政成本估算 | 估算伊比利亚机制的财政成本 |

### 数据处理脚本

| 文件 | 功能 | 描述 |
|------|------|------|
| `process_data.py` | 数据处理 | 合并和清理原始数据 |
| `fetch_data.py` | 数据获取 | 从外部数据源获取数据 |
| `fetch_oil.py` | 原油价格数据 | 获取布伦特原油价格数据 |
| `fetch_data_upgrade.py` | 数据升级 | 更新数据到2023年底 |

## 参考文献

### 核心文献
1. Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco control program. *Journal of the American Statistical Association*, 105(490), 493-505.
2. Jordà, Ò. (2005). Estimation and inference of impulse responses by local projections. *American Economic Review*, 95(1), 161-182.
3. Blanchard, O., & Galí, J. (2007). The macroeconomic effects of oil price shocks: Why are the 2000s so different from the 1970s? In *Brookings Papers on Economic Activity* (Vol. 2007, No. 1). Brookings Institution Press.
4. Fabra, N., & Reguant, M. (2014). Pass-through of wholesale electricity prices to retail: Evidence from a natural experiment. *American Economic Journal: Applied Economics*, 6(3), 87-115.
5. Gopinath, G. (2015). Emergency capital flows. *American Economic Review*, 105(5), 514-518.

### 最新文献
1. Gern, A., Schnabel, I., & Zabel, F. (2022). Energy prices and inflation: Evidence from the 2022 shock. *ECB Working Paper Series No. 2645*.
2. Lane, P. R. (2022). The euro area and the energy price shock. *ECB Blog*.
3. Schnabel, I. (2022). Monetary policy and the energy crisis. *ECB Blog*.

## 联系方式

如有问题或建议：
- 创建GitHub Issue
- 邮件联系: qingsongcui9857@gmail.com

## 许可证

MIT License - 详见LICENSE文件

## 引用

如果使用了本代码，请引用：

也可以直接使用仓库根目录的 `CITATION.cff` 进行引用导入（GitHub/Zotero 友好）。

```bibtex
@techreport{energyCrisisPolicy2026,
  title={Divergent Shields: A Comparative Assessment of the "Iberian Mechanism" and Monetary Independence during the 2022 Energy Crisis},
  author={Author Name},
  year={2026},
  institution={Institution},
  note={Python package available at: [repository URL]}
}
```

## 故障排除

### 常见问题

1. **数据文件缺失**
   ```bash
   # 检查数据文件
   ls -lh data/raw/
   ls -lh data/processed/
   ```

2. **依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip

   # 单独安装问题包
   pip install pandas numpy scipy
   ```

3. **内存不足**
   - 使用`--fast`模式跳过稳健性检验
   - 关闭其他应用程序

### 错误代码

- `Exit code 1`: 脚本执行错误，查看错误信息
- `Exit code 130`: 用户中断（Ctrl+C）
- `Timeout`: 分析超时，增加timeout参数
