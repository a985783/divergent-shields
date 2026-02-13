# Divergent Shields: Comparative Assessment of the Iberian Mechanism and Monetary Policy Independence During the 2022 Energy Crisis

Language / 语言: [中文](README.md) | English (current)

## Project Overview

This repository provides the replication package for the paper:

"Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis"

The project studies a core policy question under extreme supply shocks: whether structural market intervention can outperform monetary orthodoxy in containing inflation.

## Main Findings

1. Spain's structural shield: synthetic control evidence indicates the Iberian mechanism reduced headline inflation relative to its counterfactual path.
2. Poland's monetary penalty: local-projection results show exchange-rate depreciation amplified imported energy inflation.

## Repository Structure

```text
analysis/                # Empirical analysis scripts
data/
  raw/                   # Raw data snapshots
  processed/             # Processed panel data
paper/
  figures/               # Generated figures
  tables/                # Generated tables
scripts/                 # Data fetch and processing scripts
run_all.py               # Main pipeline runner
requirements.txt         # Python dependencies
README.md                # Chinese README
README_EN.md             # English README
REPRODUCIBILITY.md       # Reproducibility guide (EN)
REPRODUCIBILITY_ZH.md    # Reproducibility guide (ZH)
```

## Quick Start

```bash
python -m pip install -r requirements.txt

# Fast reproduction of core results
python run_all.py --fast

# Artifact verification
python scripts/verify_reproducibility.py
```

For full instructions, see `REPRODUCIBILITY.md` and `REPRODUCIBILITY_ZH.md`.

## Run Modes

```bash
# Full pipeline (including robustness)
python run_all.py

# Fast pipeline (skip optional robustness block)
python run_all.py --fast

# Step-by-step mode
python run_all.py --step
```

## Step-by-Step Pipeline

```bash
python scripts/process_data.py
python analysis/01_descriptive.py
python analysis/02_local_projections_enhanced.py
python analysis/03_synthetic_control_spain_enhanced.py
python analysis/04_scm_placebo_tests.py
python analysis/05_robustness_checks.py
python analysis/06_scm_conformal_inference.py
python analysis/07_donor_sensitivity_analysis.py
python analysis/08_pretrend_tests.py
python analysis/09_timing_robustness.py
python analysis/10_fiscal_cost_estimation.py
```

## Data and Methods

- Data sources include Eurostat, FRED, IMF, and ECB-linked series (details in `data/DATA_SOURCES.md`).
- Processed panel data output: `data/processed/merged_data.csv`.
- Core empirical methods:
  - Synthetic Control Method (SCM) for Spain policy evaluation.
  - Local Projections (LP) for Poland exchange-rate transmission.

## Outputs

- Tables are generated under `paper/tables/`.
- Figures are generated under `paper/figures/`.
- Data snapshot checksums are tracked in `data/CHECKSUMS.sha256`.

## Reproducibility and Validation

- Fast reproducibility verification:
  - `python run_all.py --fast`
  - `python scripts/verify_reproducibility.py`
- Optional data refresh from public sources:
  - `python scripts/fetch_data.py`
  - `python scripts/fetch_data_upgrade.py`
  - `python scripts/fetch_oil.py`

## Citation

Please use `CITATION.cff` for GitHub/Zotero-friendly citation import.

```bibtex
@techreport{cui2026divergentshields,
  title={Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis},
  author={Cui, Qingsong},
  year={2026},
  note={Replication package: https://github.com/a985783/divergent-shields.git}
}
```

## Contact and License

- Contact: `qingsongcui9857@gmail.com`
- License: MIT (`LICENSE`)
