# 可复现性包指南 (Reproducibility Package Guide)

语言 / Language: 中文（当前） | [English](REPRODUCIBILITY.md)

本仓库已整理为可运行的可复现性包，用于支持以下论文的研究结果：

"Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis"
（分歧的盾牌：2022年能源危机期间“伊比利亚机制”与货币政策独立性的比较评估）

## 1) 快速复现主要结果

```bash
python -m pip install -r requirements.txt
python run_all.py --fast
python scripts/verify_reproducibility.py
```

预期结果：
- 所有命令的退出代码（Exit code）均为 `0`
- 在 `paper/tables/` 和 `paper/figures/` 目录下生成相关文件
- 验证摘要显示 `ALL CHECKS PASSED`（所有检查已通过）

## 2) 完整流水线（包含稳健性检验）

```bash
python run_all.py
python scripts/verify_reproducibility.py
```

## 3) 可选：从公共来源重建数据

如果您希望在处理前刷新原始数据：

```bash
python scripts/fetch_data.py
python scripts/fetch_data_upgrade.py
python scripts/fetch_oil.py
python scripts/process_data.py
```

注意事项：
- 外部数据提供商可能会修订历史数值。
- 若要精确复现论文中的表格，必须使用相同的数据快照（Snapshot）。
- 当前快照的校验和（Checksums）存储在 `data/CHECKSUMS.sha256` 中。

## 4) 确定性与环境说明

- Python 版本：推荐 3.10+（当前代码支持 3.8+）。
- 依赖项列于 `requirements.txt` 中。
- 核心脚本不需要设置伪随机模拟种子（Pseudo-random simulation seed）。
- 依赖网络的获取脚本对于本地重新运行是可选的。

## 5) 待验证的产物 (Artifacts)

`scripts/verify_reproducibility.py` 检查的最低要求产物包括：
- 输入数据：
  - `data/processed/merged_data.csv`
  - `data/raw/prc_hicp_midx.tsv.gz`
- 输出表格（示例）：
  - `paper/tables/descriptive_stats.csv`
  - `paper/tables/fiscal_cost_estimates.csv`
  - `paper/tables/scm_enhanced_ES_HICP_Total.csv`
- 输出图表（示例）：
  - `paper/figures/scm_enhanced_ES_HICP_Total.png`
  - `paper/figures/irf_enhanced_PL_HICP_Total.png`

## 6) GitHub 上传检查清单 (Checklist)

在发布之前，请确保：
- 更新 `CITATION.cff` 中的占位符（如 `authors`, `repository-code`）。
- 确认 `LICENSE` 符合您预期的法律条款。
- 运行以下命令进行最终验证：
  - `python run_all.py --fast`
  - `python scripts/verify_reproducibility.py`
- 如果数据快照发生变化，请重新生成校验和：
  - `shasum -a 256 data/raw/* data/processed/* > data/CHECKSUMS.sha256`
