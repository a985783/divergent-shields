"""
Synthetic Difference-in-Differences (SDID) for Spain / Iberian Mechanism
Implements Arkhangelsky et al. (2021, AER) manually using scipy/numpy.

Algorithm:
  1. Time weights (omega_t): ridge regression on pre-treatment donor averages
  2. Unit weights (omega_i): SCM-style SLSQP on de-trended outcomes
  3. SDID estimator: weighted two-way DID
  4. Inference: jackknife over donors

Outputs:
  paper/tables/sdid_results_ES.csv
  paper/figures/sdid_gap_ES_HICP_Total.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import minimize
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parents[1]
DATA_FILE  = BASE / "data/processed/merged_data.csv"
TABLE_DIR  = BASE / "paper/tables"
FIGURE_DIR = BASE / "paper/figures"
TABLE_DIR.mkdir(exist_ok=True)
FIGURE_DIR.mkdir(exist_ok=True)

# ── parameters ─────────────────────────────────────────────────────────────
TREATMENT   = "ES"
# PT implements Iberian Mechanism too, so treat it as a placebo/sensitivity
# donor; primary pool excludes PT for the main estimate, includes it for
# robustness.
DONORS_MAIN = ["DE", "FR", "IT", "AT", "NL"]
DONORS_FULL = ["DE", "FR", "IT", "AT", "NL", "PT"]   # robustness
OUTCOME     = "HICP_Total"
TREAT_DATE  = pd.Timestamp("2022-06-01")
START       = pd.Timestamp("2019-01-01")
END         = pd.Timestamp("2023-12-01")
RIDGE_LAMBDA = 1e-4   # regularisation for time-weight regression


# ══════════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════════

def build_panel(df, countries, outcome, start, end):
    """Return (T×N) matrix, index=dates, columns=countries."""
    sub = df[df["geo"].isin(countries)].copy()
    sub["date"] = pd.to_datetime(sub["date"])
    sub = sub[(sub["date"] >= start) & (sub["date"] <= end)]
    panel = sub.pivot(index="date", columns="geo", values=outcome).sort_index()
    panel = panel.dropna()
    return panel


def time_weights(panel_ctrl, T0):
    """
    Compute time weights omega_t (length T_post) following Arkhangelsky 2021.
    Regress (mean of donors in last pre-period) on (mean of donors in each
    pre-period), with ridge penalty, to find which pre-periods best predict
    the post-period trend.
    """
    pre  = panel_ctrl.iloc[:T0]    # shape (T0, N)
    post = panel_ctrl.iloc[T0:]    # shape (T1, N)

    N    = pre.shape[1]
    T0_  = pre.shape[0]
    T1   = post.shape[0]

    # Target: column-mean of post periods (shape T1)
    y_post = post.mean(axis=1).values   # (T1,)

    # Feature matrix: column-mean of pre periods (shape T0)
    X_pre  = pre.mean(axis=1).values    # (T0,)

    # Simple ridge: fit time weights so that X_pre @ omega ≈ y_post
    # omega is a probability vector over pre-periods, length T0
    # We solve a constrained least-squares: min ||X_pre @ w - y_post||^2 + λ||w||^2
    # subject to w >= 0, sum(w) = T1  (Arkhangelsky normalisation)
    def loss(w):
        fitted = np.dot(X_pre, w)          # scalar (each w_t weights a pre-period mean)
        # broadcast: for each post period use the same weighted average
        resid  = y_post - fitted
        return np.dot(resid, resid) + RIDGE_LAMBDA * np.dot(w, w)

    w0 = np.ones(T0_) / T0_
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0, None)] * T0_
    res = minimize(loss, w0, method="SLSQP",
                   bounds=bounds, constraints=constraints,
                   options={"maxiter": 2000, "ftol": 1e-10})
    return res.x   # shape (T0,)


def unit_weights(panel_pre_ctrl, treated_pre):
    """
    Compute unit weights omega_i (length N_donors) via SCM SLSQP on
    de-trended pre-treatment outcomes.
    panel_pre_ctrl: (T0 × N), treated_pre: (T0,)
    """
    T0, N = panel_pre_ctrl.shape

    # De-trend: subtract column means
    ctrl_dm    = panel_pre_ctrl - panel_pre_ctrl.mean(axis=0)
    treated_dm = treated_pre   - treated_pre.mean()

    def loss(w):
        synth = ctrl_dm.values @ w
        resid = treated_dm.values - synth
        return np.dot(resid, resid)

    w0 = np.ones(N) / N
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0, None)] * N
    res = minimize(loss, w0, method="SLSQP",
                   bounds=bounds, constraints=constraints,
                   options={"maxiter": 2000, "ftol": 1e-10})
    return res.x   # shape (N,)


def sdid_estimate(panel, treat, donors, T0):
    """
    Return SDID point estimate τ and diagnostic dict.
    panel: (T × (N+1)) with treat column and donor columns
    T0: number of pre-treatment periods
    """
    Y_treat = panel[treat].values               # (T,)
    Y_ctrl  = panel[donors].values              # (T, N)

    pre_ctrl    = Y_ctrl[:T0]                   # (T0, N)
    post_ctrl   = Y_ctrl[T0:]                   # (T1, N)
    pre_treat   = Y_treat[:T0]                  # (T0,)
    post_treat  = Y_treat[T0:]                  # (T1,)
    T1          = post_ctrl.shape[0]

    # Step 1: time weights
    omega_t = time_weights(pd.DataFrame(pre_ctrl), T0)   # (T0,)

    # Step 2: unit weights on de-trended pre-period
    omega_i = unit_weights(
        pd.DataFrame(pre_ctrl, columns=donors),
        pd.Series(pre_treat)
    )                                                     # (N,)

    # Step 3: SDID estimator (weighted DID)
    # τ = (post_treat_mean - synth_post_mean) - (weighted_pre_treat_mean - weighted_synth_pre_mean)
    synth_post = post_ctrl @ omega_i                      # (T1,)
    synth_pre  = pre_ctrl  @ omega_i                      # (T0,)

    post_diff = post_treat.mean()  - synth_post.mean()
    pre_diff  = (omega_t @ pre_treat) - (omega_t @ synth_pre)
    tau       = post_diff - pre_diff

    # Gap series (post only)
    gap_post = post_treat - synth_post

    return tau, omega_i, omega_t, gap_post, synth_post, synth_pre, post_treat, pre_treat


def jackknife_se(panel, treat, donors, T0):
    """
    Jackknife SE by leave-one-donor-out.
    Returns array of leave-one-out SDID estimates.
    """
    loo_estimates = []
    for drop in donors:
        remaining = [d for d in donors if d != drop]
        if len(remaining) < 2:
            continue
        tau_loo, *_ = sdid_estimate(panel, treat, remaining, T0)
        loo_estimates.append(tau_loo)
    loo_estimates = np.array(loo_estimates)
    n   = len(loo_estimates)
    tau_bar = loo_estimates.mean()
    se  = np.sqrt((n - 1) / n * np.sum((loo_estimates - tau_bar) ** 2))
    return se, loo_estimates


def temporal_placebo_pvalue(panel, treat, donors, T0,
                            min_pre=12, min_post=6):
    """
    Temporal placebo inference following Arkhangelsky et al. (2021).

    For each possible fake treatment date t* in the pre-treatment window,
    compute SDID on the subset of data that lies entirely before the actual
    treatment date. The empirical p-value is the fraction of placebo
    |tau| values >= |tau_actual|.

    min_pre  : minimum pre-treatment periods required before t*
    min_post : minimum post-placebo periods required (t* to T0)
    """
    # Use only pre-treatment data to build the null distribution
    pre_panel = panel.iloc[:T0]
    tau_actual, *_ = sdid_estimate(panel, treat, donors, T0)

    placebo_taus = []
    for T0_fake in range(min_pre, T0 - min_post):
        try:
            tau_fake, *_ = sdid_estimate(pre_panel, treat, donors, T0_fake)
            placebo_taus.append(tau_fake)
        except Exception:
            continue

    placebo_taus = np.array(placebo_taus)
    if len(placebo_taus) == 0:
        return np.nan, placebo_taus

    n_extreme = np.sum(np.abs(placebo_taus) >= np.abs(tau_actual))
    p_val = n_extreme / len(placebo_taus)
    return p_val, placebo_taus


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def run_sdid(donors, label="main"):
    df    = pd.read_csv(DATA_FILE, low_memory=False)
    df["date"] = pd.to_datetime(df["date"])

    countries = [TREATMENT] + donors
    panel = build_panel(df, countries, OUTCOME, START, END)

    # Align columns: treatment first, then donors in fixed order
    available_donors = [d for d in donors if d in panel.columns]
    panel = panel[[TREATMENT] + available_donors]
    panel = panel.dropna()

    dates = panel.index
    T0    = (dates < TREAT_DATE).sum()

    tau, omega_i, omega_t, gap_post, synth_post, synth_pre, post_treat, pre_treat = \
        sdid_estimate(panel, TREATMENT, available_donors, T0)

    se, loo_ests = jackknife_se(panel, TREATMENT, available_donors, T0)
    ci_lo = tau - 1.96 * se
    ci_hi = tau + 1.96 * se
    t_stat = tau / se if se > 0 else np.nan

    # Temporal placebo p-value (preferred for small N)
    p_placebo, placebo_taus = temporal_placebo_pvalue(
        panel, TREATMENT, available_donors, T0)

    print(f"\n=== SDID Results [{label}] ===")
    print(f"Donors        : {available_donors}")
    print(f"SDID estimate : {tau:+.4f} pp")
    print(f"Jackknife SE  : {se:.4f}")
    print(f"95% CI        : [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"t-stat        : {t_stat:.3f}")
    print(f"Placebo N     : {len(placebo_taus)}")
    print(f"Placebo p-val : {p_placebo:.4f}")
    print(f"Unit weights  : { {d: round(w, 3) for d, w in zip(available_donors, omega_i)} }")

    # ── save CSV ──────────────────────────────────────────────────────────
    results = pd.DataFrame({
        "metric": ["SDID_estimate_pp", "Jackknife_SE", "CI_lower_95", "CI_upper_95",
                   "t_stat", "Placebo_p_value", "N_placebo", "N_donors", "T_pre", "T_post"],
        "value":  [round(tau, 4), round(se, 4), round(ci_lo, 4), round(ci_hi, 4),
                   round(t_stat, 3), round(p_placebo, 4), len(placebo_taus),
                   len(available_donors), T0, len(gap_post)]
    })
    out_csv = TABLE_DIR / f"sdid_results_ES_{label}.csv"
    results.to_csv(out_csv, index=False)

    weights_df = pd.DataFrame({
        "donor": available_donors,
        "unit_weight": [round(w, 4) for w in omega_i]
    })
    weights_df.to_csv(TABLE_DIR / f"sdid_weights_ES_{label}.csv", index=False)

    # ── gap plot ──────────────────────────────────────────────────────────
    post_dates  = dates[T0:]
    pre_dates   = dates[:T0]

    # Full synthetic series for plot
    Y_ctrl_full = panel[available_donors].values
    synth_full  = Y_ctrl_full @ omega_i
    gap_full    = panel[TREATMENT].values - synth_full

    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(TREAT_DATE, color="gray", linewidth=1.0, linestyle=":")
    ax.annotate("Iberian Mechanism\n(June 2022)",
                xy=(TREAT_DATE, ax.get_ylim()[0] if ax.get_ylim()[0] else -4),
                xytext=(pd.Timestamp("2022-09-01"), -3.5),
                fontsize=8, color="gray",
                arrowprops=dict(arrowstyle="->", color="gray", lw=0.8))

    # Pre-treatment gap (dashed)
    ax.plot(pre_dates, gap_full[:T0], color="steelblue",
            linewidth=1.5, linestyle="--", label="Pre-treatment gap")
    # Post-treatment gap (solid)
    ax.fill_between(post_dates,
                    gap_post - 1.96 * se,
                    gap_post + 1.96 * se,
                    alpha=0.15, color="steelblue", label="95% jackknife CI")
    ax.plot(post_dates, gap_post, color="steelblue",
            linewidth=2.0,
            label=f"SDID gap (τ = {tau:.2f} pp, p_placebo = {p_placebo:.3f})")

    ax.set_xlabel("")
    ax.set_ylabel("Gap (actual − synthetic Spain), pp", fontsize=10)
    ax.set_title("SDID: Headline Inflation Gap — Spain vs Synthetic Control",
                 fontsize=11, pad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    plt.xticks(rotation=30, ha="right", fontsize=8)
    ax.legend(fontsize=9, framealpha=0.8)
    ax.grid(axis="y", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    fig.savefig(FIGURE_DIR / f"sdid_gap_ES_HICP_Total_{label}.png",
                dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved: sdid_gap_ES_HICP_Total_{label}.png")

    return tau, se, loo_ests, p_placebo


if __name__ == "__main__":
    # Main estimate (5-donor pool)
    tau_main, se_main, loo_main, p_main = run_sdid(DONORS_MAIN, label="main")

    # Robustness: include PT (also has Iberian Mechanism → expect smaller effect)
    tau_full, se_full, loo_full, p_full = run_sdid(DONORS_FULL, label="with_PT")

    # Summary table combining both
    summary = pd.DataFrame({
        "specification": ["Main (excl. PT)", "With Portugal"],
        "SDID_estimate_pp": [round(tau_main, 3), round(tau_full, 3)],
        "Jackknife_SE":     [round(se_main,  3), round(se_full,  3)],
        "CI_lower_95":      [round(tau_main - 1.96*se_main, 3),
                             round(tau_full  - 1.96*se_full,  3)],
        "CI_upper_95":      [round(tau_main + 1.96*se_main, 3),
                             round(tau_full  + 1.96*se_full,  3)],
        "Placebo_p_value":  [round(p_main, 4), round(p_full, 4)],
    })
    summary.to_csv(TABLE_DIR / "sdid_results_ES.csv", index=False)
    print("\n=== Combined SDID Summary ===")
    print(summary.to_string(index=False))
    print(f"\nAll outputs written to {TABLE_DIR} and {FIGURE_DIR}")
