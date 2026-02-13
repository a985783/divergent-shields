"""
Donor Sensitivity Analysis for Synthetic Control Method
Systematic leave-one-out (LOO) analysis to assess robustness to donor pool composition
"""


# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Settings
TARGET_COUNTRY = 'ES'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'NL']
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'
VARIABLE = 'HICP_Total'

def run_scm_basic(df, target, donors, variable, start_date, intervention_date, end_date):
    """Run SCM and return key metrics"""
    pivot = df.pivot(index='date', columns='geo', values=variable)
    pivot = pivot.dropna()
    
    available_donors = [d for d in donors if d in pivot.columns]
    if target not in pivot.columns or not available_donors:
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
    w0 = np.ones(n_donors) / n_donors
    bounds = [(0, 1) for _ in range(n_donors)]
    constraints = [{'type': 'eq', 'fun': constraint_sum}]
    
    result = minimize(loss, w0, bounds=bounds, constraints=constraints, method='SLSQP')
    
    if not result.success:
        return None
    
    weights = result.x
    weight_dict = dict(zip(available_donors, weights))
    
    X_full = pivot.loc[mask_full, available_donors]
    synthetic_full = X_full.dot(weights)
    gap = pivot.loc[mask_full, target] - synthetic_full
    
    gap_post = gap[gap.index >= intervention_date]
    ate = gap_post.mean()
    rmspe_pre = np.sqrt(mean_squared_error(y_pre, X_pre.dot(weights)))
    
    return {
        'ate': ate,
        'rmspe_pre': rmspe_pre,
        'weights': weight_dict,
        'donors_used': available_donors
    }

def run_sensitivity_analysis(df):
    """Run Leave-One-Out analysis for each donor"""
    print(f"\n{'='*70}")
    print("DONOR SENSITIVITY ANALYSIS (Leave-One-Out)")
    print(f"{'='*70}")
    
    # 1. Baseline
    baseline = run_scm_basic(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE, 
                            START_DATE, INTERVENTION_DATE, END_DATE)
    
    if baseline is None:
        print("Baseline SCM failed")
        return
        
    print(f"Baseline ATE: {baseline['ate']:.4f}")
    print(f"Baseline RMSPE: {baseline['rmspe_pre']:.4f}")
    print("Baseline Weights:")
    for d, w in baseline['weights'].items():
        if w > 0.01:
            print(f"  {d}: {w:.4f}")
            
    results = []
    results.append({
        'excluded': 'None (Baseline)',
        'ate': baseline['ate'],
        'rmspe': baseline['rmspe_pre'],
        'change_pct': 0.0,
        'interpretation': 'Reference'
    })
    
    # 2. Leave-One-Out
    for donor in DONOR_POOL:
        loo_donors = [d for d in DONOR_POOL if d != donor]
        
        res = run_scm_basic(df, TARGET_COUNTRY, loo_donors, VARIABLE,
                           START_DATE, INTERVENTION_DATE, END_DATE)
        
        if res:
            change_pct = (res['ate'] - baseline['ate']) / abs(baseline['ate']) * 100
            
            interpretation = "Robust"
            if abs(change_pct) > 20: interpretation = "Sensitive"
            if abs(change_pct) > 50: interpretation = "Highly Sensitive"
            
            results.append({
                'excluded': donor,
                'ate': res['ate'],
                'rmspe': res['rmspe_pre'],
                'change_pct': change_pct,
                'interpretation': interpretation
            })
            
            print(f"Excluded {donor}: ATE={res['ate']:.4f}, RMSPE={res['rmspe_pre']:.4f}, Change={change_pct:.1f}%")
            
    # 3. Save Summary
    results_df = pd.DataFrame(results)
    output_file = os.path.join(RESULTS_DIR, "donor_loo_summary.csv")
    results_df.to_csv(output_file, index=False)
    print(f"\nSummary saved: {output_file}")
    
    # 4. Visualization
    plot_sensitivity(results_df)

def plot_sensitivity(df):
    """Plot sensitivity analysis results"""
    plt.figure(figsize=(12, 6))
    
    # Sort by ATE magnitude
    df_plot = df.copy()
    
    # Bar plot of ATEs
    bars = plt.bar(df_plot['excluded'], df_plot['ate'], 
                  color=['#1f77b4' if x == 'None (Baseline)' else '#d62728' if abs(y) > 50 else 'gray' 
                         for x, y in zip(df_plot['excluded'], df_plot['change_pct'])])
    
    plt.axhline(df_plot.loc[0, 'ate'], color='black', linestyle='--', alpha=0.5, label='Baseline Effect')
    plt.axhline(0, color='black', linewidth=1)
    
    plt.ylabel('Average Treatment Effect (Index Points)')
    plt.title('Sensitivity of Treatment Effect to Donor Exclusion', fontsize=14)
    
    # Add labels
    for bar, change in zip(bars, df_plot['change_pct']):
        height = bar.get_height()
        label = f"{change:+.0f}%" if change != 0 else "Ref"
        plt.text(bar.get_x() + bar.get_width()/2., height,
                label, ha='center', va='bottom' if height < 0 else 'top', fontsize=10, fontweight='bold')
    
    plt.grid(axis='y', alpha=0.3)
    
    # Add interpretation text
    sensitive_donors = df_plot[abs(df_plot['change_pct']) > 20]['excluded'].tolist()
    sensitive_donors = [d for d in sensitive_donors if d != 'None (Baseline)']
    
    textstr = "Interpretation:\n"
    if sensitive_donors:
        textstr += f"Results are sensitive to excluding: {', '.join(sensitive_donors)}\n"
        textstr += "This indicates these donors are essential for the counterfactual."
    else:
        textstr += "Results are robust to excluding any single donor."
        
    plt.figtext(0.5, -0.05, textstr, ha="center", fontsize=10, 
                bbox={"facecolor":"orange", "alpha":0.2, "pad":5})
    
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "donor_loo_comparison.png"), bbox_inches='tight', dpi=300)
    print(f"Plot saved: {os.path.join(FIGURES_DIR, 'donor_loo_comparison.png')}")

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
        
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    run_sensitivity_analysis(df)

if __name__ == "__main__":
    main()
