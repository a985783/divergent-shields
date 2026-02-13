# Reproducibility Package Guide

Language / 语言: English (current) | [中文](REPRODUCIBILITY_ZH.md)

This repository is organized as a runnable reproducibility package for the paper:

"Divergent Shields: A Comparative Assessment of the Iberian Mechanism and Monetary Independence during the 2022 Energy Crisis"

## 1) Reproduce Main Results Quickly

```bash
python -m pip install -r requirements.txt
python run_all.py --fast
python scripts/verify_reproducibility.py
```

Expected result:
- Exit code `0` for all commands
- Generated files under `paper/tables/` and `paper/figures/`
- Verification summary indicates `ALL CHECKS PASSED`

## 2) Full Pipeline (Including Robustness)

```bash
python run_all.py
python scripts/verify_reproducibility.py
```

## 3) Optional: Rebuild Data from Public Sources

If you want to refresh raw data before processing:

```bash
python scripts/fetch_data.py
python scripts/fetch_data_upgrade.py
python scripts/fetch_oil.py
python scripts/process_data.py
```

Notes:
- External data providers may revise historical values.
- Reproducing paper tables exactly requires using the same data snapshot.
- Current snapshot checksums are in `data/CHECKSUMS.sha256`.

## 4) Determinism and Environment

- Python version: 3.10+ recommended (3.8+ supported by current code).
- Dependencies are listed in `requirements.txt`.
- No pseudo-random simulation seed is required for the core scripts.
- Network-dependent fetching scripts are optional for local reruns.

## 5) Artifacts to Verify

Minimum required artifacts checked by `scripts/verify_reproducibility.py`:
- Input data:
  - `data/processed/merged_data.csv`
  - `data/raw/prc_hicp_midx.tsv.gz`
- Output tables (sample):
  - `paper/tables/descriptive_stats.csv`
  - `paper/tables/fiscal_cost_estimates.csv`
  - `paper/tables/scm_enhanced_ES_HICP_Total.csv`
- Output figures (sample):
  - `paper/figures/scm_enhanced_ES_HICP_Total.png`
  - `paper/figures/irf_enhanced_PL_HICP_Total.png`

## 6) GitHub Upload Checklist

Before publishing:
- Update placeholders in `CITATION.cff` (`authors`, `repository-code`).
- Confirm `LICENSE` matches your intended legal terms.
- Run:
  - `python run_all.py --fast`
  - `python scripts/verify_reproducibility.py`
- Regenerate checksums if data snapshot changed:
  - `shasum -a 256 data/raw/* data/processed/* > data/CHECKSUMS.sha256`
