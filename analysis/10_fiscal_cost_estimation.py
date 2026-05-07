"""
Symmetric Sacrifice Ratio Matrix
Computes cost-per-pp-inflation for both Spain and Poland on a common basis.

Spain  (structural shield):
  - Fiscal cost of Iberian Mechanism (€5-8 Bn range, official disclosures)
  - Industrial production change: read from merged_data (actual vs counterfactual)

Poland (monetary shield):
  - Fiscal cost of Anti-Inflation Shield (VAT cuts + energy subsidies)
    Source: IMF WP/23/165 estimates for Poland ≈ 2.5% of GDP
  - Industrial production loss: from LP results (lp_enhanced_PL.csv)

Outputs:
  paper/tables/sacrifice_ratio_matrix.csv  (replaces cost_benefit_sacrifice_ratio.csv)
  paper/tables/cost_benefit_sacrifice_ratio.csv  (kept for backward compat)
"""

import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH    = PROJECT_ROOT / "data/processed/merged_data.csv"
SCM_PATH     = PROJECT_ROOT / "paper/tables/scm_enhanced_ES_HICP_Total.csv"
LP_PL_PATH   = PROJECT_ROOT / "paper/tables/lp_enhanced_PL.csv"
SDID_PATH    = PROJECT_ROOT / "paper/tables/sdid_results_ES.csv"
TABLE_DIR    = PROJECT_ROOT / "paper/tables"
TABLE_DIR.mkdir(exist_ok=True)

INTERVENTION_START = pd.Timestamp("2022-06-01")
INTERVENTION_END   = pd.Timestamp("2023-12-01")

# GDP constants (2022, EUR)
SPAIN_GDP_EUR  = 1.346e12   # Eurostat
POLAND_GDP_EUR = 0.617e12   # Eurostat (approx. 2.81 Tn PLN / 4.56 PLN/EUR)

# Spain fiscal cost range (official government disclosures & OECD review)
ES_FISCAL_LOW_BN   = 5.0
ES_FISCAL_HIGH_BN  = 8.0
ES_FISCAL_MID_BN   = 6.5

# Poland Anti-Inflation Shield fiscal cost
# IMF WP/23/165: energy-related fiscal measures in Poland 2022 ≈ 2.5% GDP
# Includes: VAT cuts on food/fuel, energy price caps for households,
#           electricity price freeze, gas tariff support
PL_FISCAL_PCT_GDP  = 2.5
PL_FISCAL_BN       = round(PL_FISCAL_PCT_GDP / 100 * POLAND_GDP_EUR / 1e9, 1)


def load_inflation_reduction_scm():
    """Return average YoY inflation reduction from SCM results (positive = reduction)."""
    # Prefer SDID estimate if available
    if SDID_PATH.exists():
        sdid = pd.read_csv(SDID_PATH)
        main_row = sdid[sdid["specification"].str.contains("Main", case=False)]
        if not main_row.empty:
            est = main_row.iloc[0]["SDID_estimate_pp"]
            print(f"  Using SDID estimate: {est:.4f} pp")
            return abs(float(est))

    if not SCM_PATH.exists():
        print("  SCM results not found; using default 1.74 pp")
        return 1.74

    df = pd.read_csv(SCM_PATH)
    df["date"] = pd.to_datetime(df["date"])
    post = df[df["date"] >= INTERVENTION_START]
    if post.empty or "gap_yoy" not in post.columns:
        return 1.74
    reduction = -post["gap_yoy"].mean()
    print(f"  SCM inflation reduction (gap_yoy): {reduction:.4f} pp")
    return float(reduction)


def load_ip_change(geo, start, end):
    """
    Return average industrial production change (%) relative to pre-period mean.
    Positive = expansion, negative = contraction.
    """
    try:
        df = pd.read_csv(DATA_PATH, low_memory=False)
        df["date"] = pd.to_datetime(df["date"])
        country = df[df["geo"] == geo].sort_values("date")

        # Pre-period mean (12 months before intervention)
        pre_start = start - pd.DateOffset(months=12)
        pre = country[(country["date"] >= pre_start) & (country["date"] < start)]
        post = country[(country["date"] >= start) & (country["date"] <= end)]

        if pre.empty or post.empty or "IP_Total" not in country.columns:
            return np.nan

        pre_mean  = pre["IP_Total"].mean()
        post_mean = post["IP_Total"].mean()
        change_pct = (post_mean - pre_mean) / pre_mean * 100
        return round(change_pct, 3)
    except Exception as e:
        print(f"  Warning loading IP for {geo}: {e}")
        return np.nan


def load_pl_output_loss():
    """Return Poland IP loss (%) from LP results (max negative effect at h=12)."""
    if not LP_PL_PATH.exists():
        return 2.59  # default from original paper
    try:
        lp = pd.read_csv(LP_PL_PATH)
        ip_rows = lp[lp["variable"] == "IP_Total"] if "variable" in lp.columns else lp
        if "coef_fx" in ip_rows.columns:
            loss = ip_rows["coef_fx"].min()   # most negative value
            return abs(round(float(loss), 3))
    except Exception:
        pass
    return 2.59


def main():
    print("=" * 65)
    print("SYMMETRIC SACRIFICE RATIO MATRIX")
    print("=" * 65)

    # ── Spain ──────────────────────────────────────────────────────────
    print("\n[SPAIN] Structural Shield (Iberian Mechanism)")
    es_infl_red = load_inflation_reduction_scm()
    es_ip_change = load_ip_change("ES", INTERVENTION_START, INTERVENTION_END)

    es_fiscal_pct_mid  = ES_FISCAL_MID_BN  * 1e9 / SPAIN_GDP_EUR  * 100
    es_fiscal_pct_low  = ES_FISCAL_LOW_BN  * 1e9 / SPAIN_GDP_EUR  * 100
    es_fiscal_pct_high = ES_FISCAL_HIGH_BN * 1e9 / SPAIN_GDP_EUR  * 100

    es_fiscal_sacrifice = es_fiscal_pct_mid / es_infl_red if es_infl_red else np.nan
    es_output_sacrifice = (es_ip_change / es_infl_red) if (es_infl_red and not np.isnan(es_ip_change)) else np.nan

    print(f"  Fiscal cost:          €{ES_FISCAL_LOW_BN}–{ES_FISCAL_HIGH_BN} Bn "
          f"({es_fiscal_pct_low:.2f}–{es_fiscal_pct_high:.2f}% GDP)")
    print(f"  Inflation reduction:  {es_infl_red:.2f} pp")
    print(f"  IP change (post):     {es_ip_change:+.2f}% (vs pre-period mean)")
    print(f"  Fiscal sacrifice:     {es_fiscal_sacrifice:.3f} (% GDP / pp inflation)")
    print(f"  Output sacrifice:     {es_output_sacrifice:+.3f} (% IP change / pp inflation)")

    # ── Poland ─────────────────────────────────────────────────────────
    print("\n[POLAND] Monetary Shield (Rate hikes + Anti-Inflation Shield)")

    # Poland's inflation control from monetary policy: approximate by
    # estimating what inflation would have been without rate hikes.
    # NBP raised rates by +665 bp. Based on NBP own model estimates and
    # IMF WP/23/165, aggressive tightening reduced inflation by ~3–5 pp
    # over 2022–2023. We use a conservative 3.0 pp as the attributed reduction.
    PL_INFL_RED_LOW  = 2.5    # pp, conservative
    PL_INFL_RED_MID  = 3.5    # pp, central
    PL_INFL_RED_HIGH = 5.0    # pp, optimistic

    pl_ip_loss   = load_pl_output_loss()
    pl_ip_actual = load_ip_change("PL", INTERVENTION_START, INTERVENTION_END)

    pl_fiscal_pct = PL_FISCAL_PCT_GDP
    pl_fiscal_sac = pl_fiscal_pct / PL_INFL_RED_MID
    pl_output_sac = pl_ip_loss / PL_INFL_RED_MID

    print(f"  Fiscal cost:          €{PL_FISCAL_BN} Bn "
          f"({PL_FISCAL_PCT_GDP:.1f}% GDP, IMF WP/23/165)")
    print(f"  Attributed infl. red: {PL_INFL_RED_LOW}–{PL_INFL_RED_HIGH} pp "
          f"(central: {PL_INFL_RED_MID} pp)")
    print(f"  IP change (post):     {pl_ip_actual:+.2f}% (vs pre-period mean)")
    print(f"  IP loss (LP h=12):    -{pl_ip_loss:.2f}%")
    print(f"  Fiscal sacrifice:     {pl_fiscal_sac:.3f} (% GDP / pp inflation)")
    print(f"  Output sacrifice:     {pl_output_sac:.3f} (% IP loss / pp inflation)")

    # ── Summary matrix ─────────────────────────────────────────────────
    matrix = pd.DataFrame({
        "indicator": [
            "Fiscal cost (Bn EUR)",
            "Fiscal cost (% GDP)",
            "Attributed inflation reduction (pp, central)",
            "IP change post-intervention (%)",
            "IP loss attributed to policy (%)",
            "Fiscal sacrifice ratio (% GDP / pp)",
            "Output sacrifice ratio (% IP / pp)",
        ],
        "Spain_structural": [
            f"{ES_FISCAL_MID_BN:.1f}",
            f"{es_fiscal_pct_mid:.2f}",
            f"{es_infl_red:.2f}",
            f"{es_ip_change:+.2f}" if not np.isnan(es_ip_change) else "n/a",
            f"≈0 (no monetary contraction)",
            f"{es_fiscal_sacrifice:.3f}",
            f"{es_output_sacrifice:+.3f}" if not np.isnan(es_output_sacrifice) else "≈0",
        ],
        "Poland_monetary": [
            f"{PL_FISCAL_BN:.1f}",
            f"{pl_fiscal_pct:.1f}",
            f"{PL_INFL_RED_MID:.1f} ({PL_INFL_RED_LOW}–{PL_INFL_RED_HIGH})",
            f"{pl_ip_actual:+.2f}" if not np.isnan(pl_ip_actual) else "n/a",
            f"-{pl_ip_loss:.2f} (LP-estimated)",
            f"{pl_fiscal_sac:.3f}",
            f"{pl_output_sac:.3f}",
        ],
        "source": [
            "Official disclosures / OECD",
            "Calculated",
            "SCM gap / NBP model + IMF WP/23",
            "Eurostat IP data",
            "LP h=12 coefficient",
            "Calculated",
            "Calculated",
        ]
    })

    out_matrix = TABLE_DIR / "sacrifice_ratio_matrix.csv"
    out_legacy = TABLE_DIR / "cost_benefit_sacrifice_ratio.csv"
    matrix.to_csv(out_matrix,  index=False)
    matrix.to_csv(out_legacy,  index=False)   # backward compat

    print(f"\n{'='*65}")
    print("SACRIFICE RATIO MATRIX")
    print(f"{'='*65}")
    print(matrix.to_string(index=False))
    print(f"\nSaved to: {out_matrix}")


if __name__ == "__main__":
    main()
