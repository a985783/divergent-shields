# 分歧的盾牌：2022年能源危机期间"伊比利亚机制"与货币政策独立性的比较评估

语言 / Language: 中文（当前） | [English](README_EN.md)

本仓库为以下论文提供可复现性包：

"Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis"

## 主要发现

1. **西班牙的结构性盾牌**：增强合成控制法（SCM）估计，伊比利亚机制使西班牙 headline 通胀相对于合成对照组降低约 1.74 个百分点，有效将国内电价与全球边际天然气价格脱钩。
2. **波兰的货币惩罚**：局部投影（LP）识别出"顺周期汇率分量"，兹罗提贬值在 12 个月 horizon 内每 1% 使 headline 通胀额外上升约 0.36 个百分点（p=0.073）。

## 仓库结构

```
analysis/              # 实证分析脚本（Python）
data/
  raw/                 # 原始数据快照
  processed/           # 处理后的面板数据
paper/
  figures/             # 生成的图表
  tables/              # 生成的表格
scripts/               # 数据获取与处理脚本
run_all.py             # 主流水线运行器
requirements.txt       # Python 依赖
REPRODUCIBILITY_ZH.md  # 完整可复现性指南（中文）
```

## 快速开始

```bash
pip install -r requirements.txt

# 快速复现核心结果
python run_all.py --fast

# 产物完整性检查
python scripts/verify_reproducibility.py
```

完整流水线与数据刷新说明见 `REPRODUCIBILITY_ZH.md`；分析方法与输出文件说明见 `ANALYSIS_GUIDE.md`。

## 数据来源

Eurostat（HICP、工业生产）、FRED（布伦特油价、汇率）、IMF（TTF 天然气价格）、ECB。详见 `data/DATA_SOURCES.md`。

## 引用

请使用仓库根目录的 `CITATION.cff` 进行引用导入（GitHub/Zotero 友好）。

```bibtex
@techreport{cui2026divergentshields,
  title={Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis},
  author={Cui, Qingsong},
  year={2026},
  note={Replication package: https://github.com/a985783/divergent-shields}
}
```

## 联系方式与许可证

- 联系：`qingsongcui9857@gmail.com`
- 许可：MIT（见 `LICENSE`）
