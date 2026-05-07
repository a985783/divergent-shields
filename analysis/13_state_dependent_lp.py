"""
State-Dependent Local Projections (SD-LP) for Poland
Implements Auerbach & Gorodnichenko (2012) smooth-transition framework.

State variable: 12-month rolling std of DL_Gas_EUR (lagged 1 period)
Transition function: F(z) = 1 / (1 + exp(-1.5 * z_standardised))

Regression (for each horizon h, Poland only):
  p_{t+h} - p_{t-1} = F_t * beta_H_h * S_FX
                    + (1-F_t) * beta_L_h * S_FX
                    + F_t * gamma_H_h * S_Gas
                    + (1-F_t) * gamma_L_h * S_Gas
                    + delta * X_{t-1} + eps_{t+h}

Outputs:
  paper/tables/sdlp_PL_crisis_vs_normal.csv
  paper/figures/sdlp_PL_{variable}_statedep.png  (for each outcome)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[1]
DATA_FILE  = BASE / "data/processed/merged_data.csv"
TABLE_DIR  = BASE / "paper/tables"
FIGURE_DIR = BASE / "paper/figures"
TABLE_DIR.mkdir(exist_ok=True)
FIGURE_DIR.mkdir(exist_ok=True)

# ── parameters ─────────────────────────────────────────────────────────────
COUNTRY     = "PL"
MAX_HORIZON = 12
VOL_WINDOW  = 12    # months for rolling std
GAMMA_ST    = 1.5   # smooth-transition speed parameter
N_LAGS      = 2     # control lags

OUTCOMES = {
    "HICP_Total": "Headline Inflation (HICP)",
    "HICP_Core":  "Core Inflation (HICP ex. energy)",
    "IP_Total":   "Industrial Production",
}

SHOCK_FX  = "DL_XR_Local"
SHOCK_GAS = "DL_Gas_EUR"


# ══════════════════════════════════════════════════════════════════════════
def load_poland(data_file):
    df = pd.read_csv(data_file, low_memory=False)
    df["date"] = pd.to_datetime(df["date"])
    pl = df[df["geo"] == COUNTRY].copy().sort_values("date").reset_index(drop=True)

    # EA aggregate IP as external control (skip merge if already present in data)
    if "EA_IP_Total" not in pl.columns:
        ea = df[df["geo"].isin(["DE", "FR", "IT", "AT", "NL", "ES"])].copy()
        ea_ip = (ea.groupby("date")["IP_Total"]
                   .mean()
                   .reset_index()
                   .rename(columns={"IP_Total": "EA_IP_Total"}))
        pl = pl.merge(ea_ip, on="date", how="left")
    return pl


def smooth_transition(series, gamma=GAMMA_ST):
    """Standardise series then apply logistic transition F(z)."""
    mu  = series.mean()
    sig = series.std()
    z   = (series - mu) / sig
    F   = 1.0 / (1.0 + np.exp(-gamma * z))
    return F


def run_sdlp(pl, outcome_col, max_h=MAX_HORIZON, n_lags=N_LAGS):
    """
    Run state-dependent LP for a given outcome.
    Returns DataFrame with columns:
      horizon, beta_H (crisis FX), se_H, p_H,
               beta_L (normal FX), se_L, p_L,
               gamma_H (crisis Gas), se_gH, p_gH,
               gamma_L (normal Gas), se_gL, p_gL
    """
    # --- build state variable (lagged 1 period) ---
    vol_raw = pl[SHOCK_GAS].rolling(VOL_WINDOW).std().shift(1)
    F_t     = smooth_transition(vol_raw.dropna())
    # Align index with pl
    F_series = pd.Series(np.nan, index=pl.index)
    F_series.loc[F_t.index] = F_t.values

    rows = []
    for h in range(0, max_h + 1):
        # Dependent variable: cumulative change from t-1 to t+h
        y = pl[outcome_col].shift(-h) - pl[outcome_col].shift(1)

        # Build regressor matrix
        Ft   = F_series
        FXt  = pl[SHOCK_FX]
        Gast = pl[SHOCK_GAS]

        reg = pd.DataFrame({
            "F_FX":      Ft * FXt,            # crisis-state FX
            "NF_FX":     (1 - Ft) * FXt,      # normal-state FX
            "F_Gas":     Ft * Gast,            # crisis-state Gas
            "NF_Gas":    (1 - Ft) * Gast,      # normal-state Gas
        })

        # Lags of dependent variable and shocks
        for lag in range(1, n_lags + 1):
            reg[f"lag_dep_{lag}"]    = pl[outcome_col].shift(lag)
            reg[f"lag_FX_{lag}"]     = pl[SHOCK_FX].shift(lag)
            reg[f"lag_Gas_{lag}"]    = pl[SHOCK_GAS].shift(lag)

        reg["EA_IP"] = pl["EA_IP_Total"]
        reg = sm.add_constant(reg)

        data = pd.concat([y.rename("y"), reg], axis=1).dropna()
        if len(data) < 20:
            continue

        hac_lags = h + 1
        try:
            model  = sm.OLS(data["y"], data.drop(columns="y"))
            result = model.fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
        except Exception:
            continue

        def _row(coef_name):
            if coef_name not in result.params:
                return np.nan, np.nan, np.nan
            return result.params[coef_name], result.bse[coef_name], result.pvalues[coef_name]

        bH, seH, pH   = _row("F_FX")
        bL, seL, pL   = _row("NF_FX")
        gH, segH, pgH = _row("F_Gas")
        gL, segL, pgL = _row("NF_Gas")

        rows.append({
            "horizon":    h,
            "beta_crisis_FX":   bH,  "se_crisis_FX":   seH,  "p_crisis_FX":   pH,
            "beta_normal_FX":   bL,  "se_normal_FX":   seL,  "p_normal_FX":   pL,
            "gamma_crisis_Gas": gH,  "se_crisis_Gas":  segH, "p_crisis_Gas":  pgH,
            "gamma_normal_Gas": gL,  "se_normal_Gas":  segL, "p_normal_Gas":  pgL,
            "nobs": len(data),
        })

    return pd.DataFrame(rows)


def plot_sdlp(res_df, outcome_col, outcome_label, out_path):
    """Two-panel IRF: crisis state (top) vs normal state (bottom)."""
    h    = res_df["horizon"].values
    bH   = res_df["beta_crisis_FX"].values
    seH  = res_df["se_crisis_FX"].values
    bL   = res_df["beta_normal_FX"].values
    seL  = res_df["se_normal_FX"].values

    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    for ax, coef, se, title, col in [
        (axes[0], bH, seH, "High-Volatility State (Crisis)", "crimson"),
        (axes[1], bL, seL, "Low-Volatility State (Normal)",  "steelblue"),
    ]:
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.fill_between(h, coef - 1.96 * se, coef + 1.96 * se,
                        alpha=0.20, color=col)
        ax.plot(h, coef, color=col, linewidth=2.0, marker="o", markersize=4)
        ax.set_title(title, fontsize=10, pad=6)
        ax.set_ylabel("Response (pp)", fontsize=9)
        ax.grid(axis="y", linewidth=0.4, alpha=0.5)

    axes[1].set_xlabel("Horizon (months)", fontsize=9)
    fig.suptitle(f"State-Dependent LP: Poland FX Shock → {outcome_label}",
                 fontsize=11, y=1.01)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    pl = load_poland(DATA_FILE)

    all_results = []

    for col, label in OUTCOMES.items():
        if col not in pl.columns:
            print(f"[SKIP] {col} not in data")
            continue

        print(f"\n--- Running SD-LP: {col} ---")
        res = run_sdlp(pl, col)

        if res.empty:
            print(f"  No results for {col}")
            continue

        res.insert(0, "outcome", col)
        all_results.append(res)

        # Print key h=12 results
        r12 = res[res["horizon"] == 12]
        if not r12.empty:
            r12 = r12.iloc[0]
            print(f"  h=12 | crisis FX: β={r12.beta_crisis_FX:.4f} "
                  f"(p={r12.p_crisis_FX:.3f})  "
                  f"| normal FX: β={r12.beta_normal_FX:.4f} "
                  f"(p={r12.p_normal_FX:.3f})")

        # Plot
        fig_path = FIGURE_DIR / f"sdlp_PL_{col}_statedep.png"
        plot_sdlp(res, col, label, fig_path)
        print(f"  Figure saved: {fig_path.name}")

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        out_csv  = TABLE_DIR / "sdlp_PL_crisis_vs_normal.csv"
        combined.to_csv(out_csv, index=False)
        print(f"\nAll SD-LP results saved to {out_csv}")

        # Compact summary table: crisis vs normal FX at h=6 and h=12
        summary_rows = []
        for col in OUTCOMES:
            sub = combined[combined["outcome"] == col]
            for h_val in [6, 12]:
                row = sub[sub["horizon"] == h_val]
                if row.empty:
                    continue
                row = row.iloc[0]
                summary_rows.append({
                    "outcome":    col,
                    "horizon":    h_val,
                    "beta_crisis_FX":  round(row.beta_crisis_FX,  4),
                    "p_crisis_FX":     round(row.p_crisis_FX,     3),
                    "beta_normal_FX":  round(row.beta_normal_FX,  4),
                    "p_normal_FX":     round(row.p_normal_FX,     3),
                })
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(TABLE_DIR / "sdlp_PL_summary.csv", index=False)
        print("\n=== SD-LP Summary (h=6 and h=12) ===")
        print(summary_df.to_string(index=False))
    else:
        print("No results generated — check data availability.")
