"""
Conformal Inference for Synthetic Control Method
Implements quantile-based confidence intervals using placebo distribution
Following Chernozhukov et al. (2021) and Abadie (2021)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.optimize import minimize
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Config
DATA_PATH = "/Users/cuiqingsong/Documents/第三论文尝试/data/processed/merged_data.csv"
FIGURES_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/paper/figures"
RESULTS_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/paper/tables"
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Settings
TARGET_COUNTRY = 'ES'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'NL']
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'
VARIABLE = 'HICP_Total'
ALPHA = 0.05  # Significance level for 95% CI

def run_scm_return_gap(df, target, donors, variable, start_date, intervention_date, end_date):
    """Run SCM and return full gap time series"""
    pivot = df.pivot(index='date', columns='geo', values=variable)
    pivot = pivot.dropna()
    
    available_donors = [d for d in donors if d in pivot.columns]
    if target not in pivot.columns:
        return None
    
    mask_pre = (pivot.index >= start_date) & (pivot.index < intervention_date)
    mask_full = (pivot.index >= start_date) & (pivot.index <= end_date)
    
    y_pre = pivot.loc[mask_pre, target]
    X_pre = pivot.loc[mask_pre, available_donors]
    
    def loss(w):
        return np.sum((y_pre - X_pre.dot(w))**2)
    
    def constraint_sum(w):
        return np.sum(w) - 1.0
    
    n_donors = len(available_donors)
    if n_donors == 0:
        return None
    
    w0 = np.ones(n_donors) / n_donors
    bounds = [(0, 1) for _ in range(n_donors)]
    constraints = [{'type': 'eq', 'fun': constraint_sum}]
    
    result = minimize(loss, w0, bounds=bounds, constraints=constraints, method='SLSQP')
    
    if not result.success:
        return None
    
    weights = result.x
    
    X_full = pivot.loc[mask_full, available_donors]
    y_full = pivot.loc[mask_full, target]
    synthetic_full = X_full.dot(weights)
    
    gap = y_full - synthetic_full
    rmspe_pre = np.sqrt(mean_squared_error(y_pre, X_pre.dot(weights)))
    
    return {
        'gap': gap,
        'actual': y_full,
        'synthetic': synthetic_full,
        'rmspe_pre': rmspe_pre,
        'weights': dict(zip(available_donors, weights))
    }

def compute_placebo_gaps(df):
    """
    Run SCM for all donors as placebo treated units
    Returns DataFrame with placebo gaps
    """
    print(f"\n{'='*70}")
    print("COMPUTING PLACEBO DISTRIBUTION FOR CONFORMAL INFERENCE")
    print(f"{'='*70}")
    
    placebo_gaps = {}
    placebo_rmspes = {}
    
    # Get actual treatment
    print(f"\nActual treated unit: {TARGET_COUNTRY}")
    actual_result = run_scm_return_gap(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE,
                                       START_DATE, INTERVENTION_DATE, END_DATE)
    
    if actual_result is None:
        print("Failed to run actual SCM")
        return None, None
    
    actual_gap = actual_result['gap']
    actual_rmspe = actual_result['rmspe_pre']
    
    print(f"Actual pre-RMSPE: {actual_rmspe:.4f}")
    print(f"Actual post-treatment mean gap: {actual_gap[actual_gap.index >= INTERVENTION_DATE].mean():.4f}")
    
    # Run placebo tests
    print(f"\nRunning placebo tests for {len(DONOR_POOL)} donors...")
    
    for i, donor in enumerate(DONOR_POOL):
        print(f"  [{i+1}/{len(DONOR_POOL)}] Placebo: {donor}")
        
        # Create new donor pool excluding current placebo
        new_donors = [d for d in DONOR_POOL if d != donor]
        
        placebo_result = run_scm_return_gap(df, donor, new_donors, VARIABLE,
                                           START_DATE, INTERVENTION_DATE, END_DATE)
        
        if placebo_result is not None:
            placebo_gaps[donor] = placebo_result['gap']
            placebo_rmspes[donor] = placebo_result['rmspe_pre']
            print(f"    Pre-RMSPE: {placebo_result['rmspe_pre']:.4f}")
        else:
            print(f"    Failed to converge")
    
    return actual_gap, placebo_gaps, actual_rmspe, placebo_rmspes

def conformal_inference(actual_gap, placebo_gaps, alpha=0.05):
    """
    Construct conformal prediction intervals
    
    Method: For each time point, construct CI using quantiles of placebo distribution
    """
    print(f"\n{'='*70}")
    print("CONFORMAL INFERENCE")
    print(f"{'='*70}")
    
    # Convert placebo gaps to DataFrame
    placebo_df = pd.DataFrame(placebo_gaps)
    
    # Ensure same index
    common_index = actual_gap.index.intersection(placebo_df.index)
    actual_gap = actual_gap.loc[common_index]
    placebo_df = placebo_df.loc[common_index]
    
    # Compute quantiles at each time point
    ci_lower = placebo_df.quantile(alpha/2, axis=1)
    ci_upper = placebo_df.quantile(1-alpha/2, axis=1)
    
    # Point-wise coverage
    coverage = ((actual_gap >= ci_lower) & (actual_gap <= ci_upper)).mean()
    
    print(f"\nConfidence Level: {(1-alpha)*100}%")
    print(f"Point-wise Coverage: {coverage*100:.1f}%")
    
    # Post-intervention statistics
    post_mask = actual_gap.index >= INTERVENTION_DATE
    post_gap = actual_gap[post_mask]
    post_ci_lower = ci_lower[post_mask]
    post_ci_upper = ci_upper[post_mask]
    
    # Check if zero is in CI (significance test)
    zero_in_ci = ((post_ci_lower < 0) & (post_ci_upper > 0)).mean()
    
    print(f"\nPost-Intervention Statistics:")
    print(f"  Mean gap: {post_gap.mean():.4f}")
    print(f"  Mean CI lower: {post_ci_lower.mean():.4f}")
    print(f"  Mean CI upper: {post_ci_upper.mean():.4f}")
    print(f"  Proportion with zero in CI: {zero_in_ci*100:.1f}%")
    
    if zero_in_ci < 0.5:
        print(f"  ✓ Effect is SIGNIFICANT (zero not in CI for most periods)")
    else:
        print(f"  ✗ Effect is NOT SIGNIFICANT (zero in CI for most periods)")
    
    return {
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'coverage': coverage,
        'significant': zero_in_ci < 0.5,
        'post_mean_gap': post_gap.mean(),
        'post_mean_ci_lower': post_ci_lower.mean(),
        'post_mean_ci_upper': post_ci_upper.mean()
    }

def plot_conformal_results(actual_gap, ci_lower, ci_upper, intervention_date):
    """
    Plot actual gap with conformal confidence bands
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Full period with confidence bands
    ax1 = axes[0]
    
    # Confidence bands
    ax1.fill_between(actual_gap.index, ci_lower, ci_upper, 
                     color='lightblue', alpha=0.3, label='95% Conformal CI')
    
    # Actual gap
    ax1.plot(actual_gap.index, actual_gap, color='#d62728', linewidth=2.5, 
             label='Actual Treatment Effect', zorder=3)
    
    # Zero line
    ax1.axhline(0, color='black', linestyle='-', linewidth=0.8)
    
    # Intervention line
    ax1.axvline(pd.to_datetime(intervention_date), color='gray', linestyle='--', 
                linewidth=2, label='Intervention')
    
    # Shading for post-intervention
    post_idx = actual_gap.index >= intervention_date
    ax1.axvspan(pd.to_datetime(intervention_date), actual_gap.index[-1], 
                alpha=0.1, color='yellow', label='Post-Intervention')
    
    ax1.set_title('Treatment Effect with 95% Conformal Confidence Bands', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Gap (Actual - Synthetic)', fontsize=11)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Statistics box
    post_mask = actual_gap.index >= intervention_date
    post_gap = actual_gap[post_mask]
    post_ci_lower = ci_lower[post_mask]
    post_ci_upper = ci_upper[post_mask]
    
    textstr = '\n'.join([
        f'Post-Intervention:',
        f'Mean Effect: {post_gap.mean():.3f}',
        f'95% CI: [{post_ci_lower.mean():.3f}, {post_ci_upper.mean():.3f}]',
        f'Significant: {"Yes" if post_ci_upper.mean() < 0 else "No"}'
    ])
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    # Plot 2: Post-intervention zoom
    ax2 = axes[1]
    
    post_actual = actual_gap[post_mask]
    
    ax2.fill_between(post_actual.index, post_ci_lower, post_ci_upper,
                     color='lightblue', alpha=0.3, label='95% Conformal CI')
    
    ax2.plot(post_actual.index, post_actual, 'o-', color='#d62728', 
             linewidth=2.5, markersize=5, label='Treatment Effect')
    
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.8)
    
    ax2.set_title('Post-Intervention Period (Detailed View)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=11)
    ax2.set_ylabel('Gap (Actual - Synthetic)', fontsize=11)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_file = os.path.join(FIGURES_DIR, f"scm_conformal_inference_{VARIABLE}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nConformal inference plot saved: {output_file}")

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found: {DATA_PATH}")
        return
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Step 1: Compute placebo distribution
    actual_gap, placebo_gaps, actual_rmspe, placebo_rmspes = compute_placebo_gaps(df)
    
    if actual_gap is None:
        print("Failed to compute placebo distribution")
        return
    
    # Step 2: Conformal inference
    ci_results = conformal_inference(actual_gap, placebo_gaps, alpha=ALPHA)
    
    # Step 3: Plot results
    plot_conformal_results(actual_gap, ci_results['ci_lower'], ci_results['ci_upper'], 
                          INTERVENTION_DATE)
    
    # Step 4: Save results
    results_df = pd.DataFrame({
        'date': actual_gap.index,
        'actual_gap': actual_gap.values,
        'ci_lower': ci_results['ci_lower'].values,
        'ci_upper': ci_results['ci_upper'].values,
        'zero_in_ci': (ci_results['ci_lower'].values < 0) & (ci_results['ci_upper'].values > 0)
    })
    
    output_file = os.path.join(RESULTS_DIR, f"scm_conformal_inference_{VARIABLE}.csv")
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved: {output_file}")
    
    # Summary statistics
    summary = {
        'variable': VARIABLE,
        'target': TARGET_COUNTRY,
        'alpha': ALPHA,
        'coverage': ci_results['coverage'],
        'post_mean_gap': ci_results['post_mean_gap'],
        'post_ci_lower': ci_results['post_mean_ci_lower'],
        'post_ci_upper': ci_results['post_mean_ci_upper'],
        'significant': ci_results['significant']
    }
    
    summary_file = os.path.join(RESULTS_DIR, f"scm_conformal_summary_{VARIABLE}.csv")
    pd.DataFrame([summary]).to_csv(summary_file, index=False)
    print(f"Summary saved: {summary_file}")
    
    print(f"\n{'='*70}")
    print("CONFORMAL INFERENCE COMPLETED")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
