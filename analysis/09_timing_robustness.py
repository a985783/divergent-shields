"""
Timing Robustness Analysis
Tests sensitivity of SCM results to alternative intervention dates
to address endogeneity and anticipation concerns
"""


# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'
VARIABLE = 'HICP_Total'

# Alternative dates to test
DATES_TO_TEST = {
    '2022-03-01': 'War Start/Initial Discussion',
    '2022-04-26': 'General Agreement Proposal',
    '2022-06-01': 'Official Implementation (Baseline)',
    '2022-07-01': 'Full Operation'
}

def run_scm_at_date(df, intervention_date):
    """Run SCM with a specific intervention date"""
    pivot = df.pivot(index='date', columns='geo', values=VARIABLE).dropna()
    
    available_donors = [d for d in DONOR_POOL if d in pivot.columns]
    
    mask_pre = (pivot.index >= START_DATE) & (pivot.index < intervention_date)
    mask_full = (pivot.index >= START_DATE) & (pivot.index <= END_DATE)
    
    y_pre = pivot.loc[mask_pre, TARGET_COUNTRY]
    X_pre = pivot.loc[mask_pre, available_donors]
    
    def loss(w):
        return np.sum((y_pre - X_pre.dot(w))**2)
    
    def constraint_sum(w):
        return np.sum(w) - 1.0
    
    n_donors = len(available_donors)
    w0 = np.ones(n_donors) / n_donors
    
    result = minimize(loss, w0, bounds=[(0,1)]*n_donors, 
                     constraints=[{'type':'eq', 'fun':constraint_sum}], method='SLSQP')
    
    if not result.success:
        return None
        
    weights = result.x
    X_full = pivot.loc[mask_full, available_donors]
    synthetic = X_full.dot(weights)
    gap = pivot.loc[mask_full, TARGET_COUNTRY] - synthetic
    
    # Calculate post-intervention effect relative to THIS date
    gap_post = gap[gap.index >= intervention_date]
    ate = gap_post.mean()
    rmspe_pre = np.sqrt(mean_squared_error(y_pre, X_pre.dot(weights)))
    
    return {
        'ate': ate,
        'rmspe': rmspe_pre,
        'gap': gap,
        'weights': weights
    }

def run_timing_analysis(df):
    """Test all dates"""
    print(f"\n{'='*70}")
    print("TIMING ROBUSTNESS ANALYSIS")
    print(f"{'='*70}")
    
    results = []
    
    for date_str, desc in DATES_TO_TEST.items():
        print(f"\nTesting Intervention Date: {date_str} ({desc})")
        res = run_scm_at_date(df, date_str)
        
        if res:
            print(f"  Pre-RMSPE: {res['rmspe']:.4f}")
            print(f"  Estimated Effect (ATE): {res['ate']:.4f}")
            
            results.append({
                'date': date_str,
                'description': desc,
                'rmspe': res['rmspe'],
                'ate': res['ate']
            })
            
    # Save results
    res_df = pd.DataFrame(results)
    output_file = os.path.join(RESULTS_DIR, "timing_robustness_summary.csv")
    res_df.to_csv(output_file, index=False)
    print(f"\nSummary saved: {output_file}")
    
    plot_timing_robustness(res_df)

def plot_timing_robustness(df):
    """Plot ATE stability across dates"""
    plt.figure(figsize=(10, 6))
    
    # Create numeric index for plotting
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values('date_dt')
    
    plt.plot(df['date'], df['ate'], 'o-', linewidth=2, markersize=8)
    
    # Add labels
    for i, row in df.iterrows():
        plt.text(row['date'], row['ate']+0.1, 
                 f"{row['ate']:.2f}\n({row['description']})", 
                 ha='center', va='bottom', fontsize=9, rotation=0)
        
    plt.axhline(df[df['date'] == '2022-06-01']['ate'].values[0], 
                color='gray', linestyle='--', alpha=0.5, label='Baseline')
    
    plt.title('Sensitivity of Treatment Effect to Intervention Timing')
    plt.ylabel('Average Treatment Effect (Index Points)')
    plt.xlabel('Assumed Intervention Date')
    plt.grid(True, alpha=0.3)
    plt.ylim(min(df['ate'])-1, max(df['ate'])+1)
    
    plt.savefig(os.path.join(FIGURES_DIR, "timing_robustness.png"), dpi=300, bbox_inches='tight')
    print(f"Plot saved: {os.path.join(FIGURES_DIR, 'timing_robustness.png')}")

def main():
    if not os.path.exists(DATA_PATH): return
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    run_timing_analysis(df)

if __name__ == "__main__":
    main()
