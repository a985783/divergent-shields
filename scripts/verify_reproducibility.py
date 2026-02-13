#!/usr/bin/env python3
"""Lightweight reproducibility checks for the repository."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_INPUTS = [
    ROOT / "data/processed/merged_data.csv",
    ROOT / "data/raw/prc_hicp_midx.tsv.gz",
]

REQUIRED_TABLES = [
    ROOT / "paper/tables/descriptive_stats.csv",
    ROOT / "paper/tables/fiscal_cost_estimates.csv",
    ROOT / "paper/tables/scm_enhanced_ES_HICP_Total.csv",
]

REQUIRED_FIGURES = [
    ROOT / "paper/figures/scm_enhanced_ES_HICP_Total.png",
    ROOT / "paper/figures/irf_enhanced_PL_HICP_Total.png",
]


def check_file(path: Path) -> bool:
    if not path.exists():
        print(f"[FAIL] Missing: {path.relative_to(ROOT)}")
        return False
    if path.is_file() and path.stat().st_size == 0:
        print(f"[FAIL] Empty file: {path.relative_to(ROOT)}")
        return False
    print(f"[ OK ] {path.relative_to(ROOT)}")
    return True


def check_output_volume() -> bool:
    tables_dir = ROOT / "paper/tables"
    figures_dir = ROOT / "paper/figures"

    if not tables_dir.exists() or not figures_dir.exists():
        print("[FAIL] Output directories paper/tables or paper/figures are missing")
        return False

    num_tables = len([p for p in tables_dir.iterdir() if p.is_file()])
    num_figures = len([p for p in figures_dir.iterdir() if p.is_file()])
    print(f"[INFO] table files: {num_tables}")
    print(f"[INFO] figure files: {num_figures}")

    if num_tables < 5 or num_figures < 5:
        print("[FAIL] Output volume too small; pipeline may not have run correctly")
        return False

    return True


def main() -> int:
    print("== Reproducibility Verification ==")
    os.chdir(ROOT)

    ok = True

    print("\n[1/4] Checking required input files")
    for path in REQUIRED_INPUTS:
        ok = check_file(path) and ok

    print("\n[2/4] Checking required table artifacts")
    for path in REQUIRED_TABLES:
        ok = check_file(path) and ok

    print("\n[3/4] Checking required figure artifacts")
    for path in REQUIRED_FIGURES:
        ok = check_file(path) and ok

    print("\n[4/4] Checking output volume")
    ok = check_output_volume() and ok

    print("\n== Verification Summary ==")
    if ok:
        print("ALL CHECKS PASSED")
        return 0

    print("CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
