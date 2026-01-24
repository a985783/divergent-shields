"""
Enhanced Synthetic Control Method for Spain's Iberian Mechanism
Implements multidimensional predictors and statistical inference
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

# Synthetic Control Settings
TARGET_COUNTRY = 'ES'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'NL']  # Removed PT due to high correlation with ES
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'

# Predictor variables for SCM (multidimensional)
PREDICTOR_VARS = {
    'outcome': ['HICP_Total', 'HICP_Energy', 'CP0451'],  # Multiple outcome variables
    'economic': ['IP_Total'],  # Industrial production
    'energy': ['DL_Gas_EUR'],  # Gas price exposure
}

def calculate_predictors(df, country, start_date, intervention_date):
    """
    Calculate multidimensional predictors for SCM
    Includes pre-intervention means, trends, and energy structure
    """
    sub_df = df[(df['geo'] == country) & 
                (df['date'] >= start_date) & 
                (df['date'] < intervention_date)].copy()
    
    if sub_df.empty:
        return None
    
    predictors = {}
    
    # 1. Outcome variables (pre-intervention means) - ensure all exist
    for var in PREDICTOR_VARS['outcome']:
        col_name_mean = f'{var}_mean'
        col_name_trend = f'{var}_trend'
        
        if var in sub_df.columns and not sub_df[var].isna().all():
            predictors[col_name_mean] = sub_df[var].mean()
            if len(sub_df[var].dropna()) > 1:
                predictors[col_name_trend] = sub_df[var].iloc[-1] - sub_df[var].iloc[0]
            else:
                predictors[col_name_trend] = 0
        else:
            # Fill with defaults if missing
            predictors[col_name_mean] = 0
            predictors[col_name_trend] = 0
    
    # 2. Economic controls - ensure all exist
    for var in PREDICTOR_VARS['economic']:
        col_name = f'{var}_mean'
        if var in sub_df.columns and not sub_df[var].isna().all():
            predictors[col_name] = sub_df[var].mean()
        else:
            predictors[col_name] = 0
    
    # 3. Energy exposure (gas price correlation)
    if 'DL_Gas_EUR' in sub_df.columns and 'HICP_Energy' in sub_df.columns:
        valid_data = sub_df[['DL_Gas_EUR', 'HICP_Energy']].dropna()
        if len(valid_data) > 10:
            predictors['gas_energy_corr'] = valid_data['DL_Gas_EUR'].corr(valid_data['HICP_Energy'])
        else:
            predictors['gas_energy_corr'] = 0
    else:
        predictors['gas_energy_corr'] = 0
    
    # 4. Volatility measures
    if 'HICP_Total' in sub_df.columns and not sub_df['HICP_Total'].isna().all():
        predictors['inflation_volatility'] = sub_df['HICP_Total'].std()
    else:
        predictors['inflation_volatility'] = 0
    
    # Ensure all predictors are finite
    for key, value in predictors.items():
        if not np.isfinite(value):
            predictors[key] = 0
    
    return predictors

def enhanced_synthetic_control(df, target, donors, variable, start_date, intervention_date, end_date):
    """
    Enhanced SCM with multidimensional predictors and diagnostic statistics
    """
    print(f"\n{'='*60}")
    print(f"Running Enhanced SCM for {variable}")
    print(f"{'='*60}")
    
    # Prepare data
    pivot = df.pivot(index='date', columns='geo', values=variable)
    pivot = pivot.dropna()
    
    available_donors = [d for d in donors if d in pivot.columns]
    if target not in pivot.columns:
        print(f"Target {target} not found in data")
        return None
    
    print(f"Target: {target}")
    print(f"Donor pool: {available_donors}")
    
    # Time masks
    mask_pre = (pivot.index >= start_date) & (pivot.index < intervention_date)
    mask_post = (pivot.index >= intervention_date) & (pivot.index <= end_date)
    mask_full = (pivot.index >= start_date) & (pivot.index <= end_date)
    
    # 1. Calculate multidimensional predictors for target and donors
    print("\nCalculating multidimensional predictors...")
    target_predictors = calculate_predictors(df, target, start_date, intervention_date)
    
    donor_predictors = {}
    for donor in available_donors:
        donor_predictors[donor] = calculate_predictors(df, donor, start_date, intervention_date)
    
    # 2. Build predictor matrix
    predictor_names = list(target_predictors.keys())
    print(f"Predictor variables: {predictor_names}")
    
    # Target predictor vector
    y_pred = np.array([target_predictors[name] for name in predictor_names])
    
    # Donor predictor matrix
    X_pred = np.array([
        [donor_predictors[donor][name] for name in predictor_names]
        for donor in available_donors
    ])
    
    # 3. Optimize weights using pre-intervention outcome fit AND predictor fit
    def combined_loss(w):
        # Outcome fit (primary objective)
        y_pre_outcome = pivot.loc[mask_pre, target]
        X_pre_outcome = pivot.loc[mask_pre, available_donors]
        outcome_loss = np.sum((y_pre_outcome - X_pre_outcome.dot(w))**2)
        
        # Predictor fit (secondary objective)
        # X_pred shape: (n_donors, n_predictors)
        # We want: y_pred (n_predictors,) ~ w (n_donors,) dot X_pred (n_donors, n_predictors)
        # Which gives: w.T @ X_pred
        predicted_predictors = w @ X_pred  # Shape: (n_predictors,)
        predictor_loss = np.sum((y_pred - predicted_predictors)**2)
        
        # Combined loss (can adjust weights)
        return outcome_loss + 0.5 * predictor_loss
    
    # Constraints: weights sum to 1, non-negative
    def constraint_sum(w):
        return np.sum(w) - 1.0
    
    n_donors = len(available_donors)
    w0 = np.ones(n_donors) / n_donors
    bounds = [(0, 1) for _ in range(n_donors)]
    constraints = [{'type': 'eq', 'fun': constraint_sum}]
    
    # Optimization
    result = minimize(combined_loss, w0, bounds=bounds, constraints=constraints, 
                     method='SLSQP', options={'disp': True, 'maxiter': 1000})
    
    if not result.success:
        print(f"Optimization failed: {result.message}")
        return None
    
    weights = result.x
    
    # 4. Calculate diagnostics
    print("\n" + "="*60)
    print("MODEL DIAGNOSTICS")
    print("="*60)
    
    # Pre-intervention RMSPE
    y_pre = pivot.loc[mask_pre, target]
    X_pre = pivot.loc[mask_pre, available_donors]
    synthetic_pre = X_pre.dot(weights)
    
    rmspe_pre = np.sqrt(mean_squared_error(y_pre, synthetic_pre))
    print(f"Pre-intervention RMSPE: {rmspe_pre:.4f}")
    
    # Pre-intervention MAPE
    mape_pre = np.mean(np.abs((y_pre - synthetic_pre) / y_pre)) * 100
    print(f"Pre-intervention MAPE: {mape_pre:.2f}%")
    
    # R-squared
    ss_res = np.sum((y_pre - synthetic_pre)**2)
    ss_tot = np.sum((y_pre - np.mean(y_pre))**2)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"Pre-intervention R²: {r_squared:.4f}")
    
    # Weight distribution
    print(f"\nOptimal Weights:")
    for donor, weight in zip(available_donors, weights):
        print(f"  {donor}: {weight:.4f}")
    
    effective_donors = np.sum(weights > 0.01)
    print(f"Effective donors (weight > 1%): {effective_donors}")
    
    max_weight = np.max(weights)
    dominant_donor = available_donors[np.argmax(weights)]
    print(f"Dominant donor: {dominant_donor} ({max_weight:.2%})")
    
    # 5. Construct synthetic control
    X_full = pivot.loc[mask_full, available_donors]
    y_full = pivot.loc[mask_full, target]
    synthetic_full = X_full.dot(weights)
    
    # 6. Calculate post-intervention effects
    gap = y_full - synthetic_full
    gap_post = gap[gap.index >= intervention_date]
    
    # Average treatment effect
    ate = gap_post.mean()
    ate_std = gap_post.std()
    
    print(f"\n{'='*60}")
    print("TREATMENT EFFECT ESTIMATES")
    print("="*60)
    print(f"Average Treatment Effect (post-intervention): {ate:.4f}")
    print(f"Standard deviation of effect: {ate_std:.4f}")
    print(f"Number of post-intervention periods: {len(gap_post)}")
    
    # YoY inflation effect
    if variable == 'HICP_Total':
        y_full_yoy = y_full.pct_change(12) * 100
        synthetic_yoy = synthetic_full.pct_change(12) * 100
        gap_yoy = y_full_yoy - synthetic_yoy
        gap_yoy_post = gap_yoy[gap_yoy.index >= intervention_date]
        
        ate_yoy = gap_yoy_post.mean()
        ate_yoy_std = gap_yoy_post.std()
        
        print(f"Average effect on YoY inflation: {ate_yoy:.2f} percentage points")
        print(f"Standard deviation: {ate_yoy_std:.2f}")
    
    # 7. Save results
    results_df = pd.DataFrame({
        'date': y_full.index,
        'actual': y_full.values,
        'synthetic': synthetic_full.values,
        'gap': gap.values
    })
    
    if variable == 'HICP_Total':
        results_df['actual_yoy'] = y_full_yoy.values
        results_df['synthetic_yoy'] = synthetic_yoy.values
        results_df['gap_yoy'] = gap_yoy.values
    
    # Save to CSV
    output_file = os.path.join(RESULTS_DIR, f"scm_enhanced_{target}_{variable}.csv")
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # 8. Plotting
    plot_scm_results(y_full, synthetic_full, gap, intervention_date, 
                    variable, target, weights, available_donors, rmspe_pre, ate_yoy if variable == 'HICP_Total' else None)
    
    # Return diagnostics
    return {
        'weights': dict(zip(available_donors, weights)),
        'rmspe_pre': rmspe_pre,
        'mape_pre': mape_pre,
        'r_squared': r_squared,
        'ate': ate,
        'ate_yoy': ate_yoy if variable == 'HICP_Total' else None,
        'post_periods': len(gap_post)
    }

def plot_scm_results(actual, synthetic, gap, intervention_date, variable, target, weights, donors, rmspe_pre, ate_yoy=None):
    """
    Create publication-quality SCM plots with confidence bands and diagnostics
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Enhanced Synthetic Control Analysis: {target} vs Synthetic {target}\nVariable: {variable}', 
                 fontsize=14, fontweight='bold')
    
    # Plot 1: Actual vs Synthetic (Levels)
    ax1 = axes[0, 0]
    ax1.plot(actual.index, actual, label=f'Actual {target}', color='#d62728', linewidth=2.5)
    ax1.plot(synthetic.index, synthetic, label=f'Synthetic {target}', color='#1f77b4', 
             linestyle='--', linewidth=2)
    ax1.axvline(pd.to_datetime(intervention_date), color='gray', linestyle=':', 
                linewidth=2, label='Intervention')
    
    # Shade treatment effect
    post_idx = actual.index >= intervention_date
    ax1.fill_between(actual.index[post_idx], actual[post_idx], synthetic[post_idx], 
                     where=(actual[post_idx] < synthetic[post_idx]), 
                     color='green', alpha=0.2, label='Inflation Reduction')
    
    ax1.set_title(f'Index Levels\nPre-RMSPE: {rmspe_pre:.3f}, R²: {calculate_r_squared(actual[actual.index < intervention_date], synthetic[actual.index < intervention_date]):.3f}')
    ax1.set_ylabel('Index (2015=100)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Gap (Actual - Synthetic)
    ax2 = axes[0, 1]
    ax2.plot(gap.index, gap, color='#2ca02c', linewidth=2)
    ax2.axhline(0, color='black', linestyle='-', linewidth=0.8)
    ax2.axvline(pd.to_datetime(intervention_date), color='gray', linestyle=':', linewidth=2)
    
    # Add post-intervention statistics
    gap_post = gap[gap.index >= intervention_date]
    ax2.text(0.05, 0.95, f"Post-intervention:\nMean gap: {gap_post.mean():.2f}\nStd: {gap_post.std():.2f}", 
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax2.set_title('Treatment Effect Gap (Actual - Synthetic)')
    ax2.set_ylabel('Index Points')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: YoY Inflation (if applicable)
    if ate_yoy is not None:
        ax3 = axes[1, 0]
        actual_yoy = actual.pct_change(12) * 100
        synthetic_yoy = synthetic.pct_change(12) * 100
        
        ax3.plot(actual_yoy.index, actual_yoy, label=f'Actual {target}', color='#d62728', linewidth=2.5)
        ax3.plot(synthetic_yoy.index, synthetic_yoy, label=f'Synthetic {target}', color='#1f77b4', 
                 linestyle='--', linewidth=2)
        ax3.axvline(pd.to_datetime(intervention_date), color='gray', linestyle=':', linewidth=2)
        
        gap_yoy = actual_yoy - synthetic_yoy
        gap_yoy_post = gap_yoy[gap_yoy.index >= intervention_date]
        
        ax3.text(0.05, 0.95, f"Avg effect on YoY inflation:\n{gap_yoy_post.mean():.2f} pp", 
                 transform=ax3.transAxes, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        ax3.set_title('Year-over-Year Inflation Rate')
        ax3.set_ylabel('YoY % Change')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        axes[1, 0].axis('off')
    
    # Plot 4: Synthetic Weights
    ax4 = axes[1, 1]
    weights_list = [weights[i] for i in range(len(donors)) if weights[i] > 0.01]
    donors_list = [donors[i] for i in range(len(donors)) if weights[i] > 0.01]
    
    if weights_list:
        colors = plt.cm.Set3(np.linspace(0, 1, len(weights_list)))
        wedges, texts, autotexts = ax4.pie(weights_list, labels=donors_list, autopct='%1.1f%%', 
                                           colors=colors, startangle=90)
        ax4.set_title('Synthetic Control Weights (donors > 1%)')
    else:
        ax4.text(0.5, 0.5, 'No donors with weight > 1%', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Synthetic Control Weights')
    
    plt.tight_layout()
    
    # Save plot
    output_plot = os.path.join(FIGURES_DIR, f"scm_enhanced_{target}_{variable}.png")
    plt.savefig(output_plot, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Enhanced plot saved to: {output_plot}")

def calculate_r_squared(y_true, y_pred):
    """Calculate R-squared"""
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1 - (ss_res / ss_tot)

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Variables to analyze
    variables = [
        ('HICP_Total', 'Headline Inflation'),
        ('CP0451', 'Electricity Prices'),
        ('HICP_Energy', 'Energy Inflation')
    ]
    
    # Store diagnostics
    diagnostics_summary = []
    
    for var_code, var_name in variables:
        if var_code not in df.columns:
            print(f"Variable {var_code} not found in data")
            continue
        
        diag = enhanced_synthetic_control(df, TARGET_COUNTRY, DONOR_POOL, var_code, 
                                         START_DATE, INTERVENTION_DATE, END_DATE)
        
        if diag:
            diag['variable'] = var_code
            diag['variable_name'] = var_name
            diagnostics_summary.append(diag)
    
    # Save diagnostics summary
    if diagnostics_summary:
        diag_df = pd.DataFrame(diagnostics_summary)
        diag_file = os.path.join(RESULTS_DIR, "scm_diagnostics_summary.csv")
        diag_df.to_csv(diag_file, index=False)
        print(f"\n{'='*60}")
        print("DIAGNOSTICS SUMMARY SAVED")
        print(f"{'='*60}")
        print(diag_df[['variable', 'variable_name', 'rmspe_pre', 'r_squared', 
                       'ate', 'ate_yoy', 'post_periods']].to_string(index=False))
        print(f"\nSaved to: {diag_file}")

if __name__ == "__main__":
    main()
