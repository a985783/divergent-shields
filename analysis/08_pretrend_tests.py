"""
Pre-Trend Validation Tests
Formal statistical tests for parallel trends assumption and event study validation
"""


# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import os
from scipy import stats

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Settings
TARGET_COUNTRY = 'ES'
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
PRE_PERIOD_END = '2022-05-01'
VARIABLE = 'HICP_Total'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'NL']

# Donor weights from SCM (Hardcoded based on enhanced SCM results for consistency)
# Ideally these should be loaded, but for robustness testing we use the optimized weights
WEIGHTS = {'DE': 0.483, 'FR': 0.324, 'IT': 0.181, 'NL': 0.012, 'AT': 0.0}

def prepare_data(df, target, donors, variable, start_date, pre_end_date):
    """Prepare data for treating pre-trends"""
    pivot = df.pivot(index='date', columns='geo', values=variable)
    
    # Construct Synthetic Control Series
    donor_data = pivot[list(WEIGHTS.keys())]
    weights_array = np.array([WEIGHTS[d] for d in donor_data.columns])
    synthetic = donor_data.dot(weights_array)
    
    actual = pivot[target]
    
    # Combine into dataframe
    data = pd.DataFrame({'Actual': actual, 'Synthetic': synthetic})
    data = data[(data.index >= start_date) & (data.index <= pre_end_date)]
    data = data.dropna()
    
    return data

def diff_in_slopes_test(data):
    """
    Test 1: Difference in Slopes
    Regress difference (Actual - Synthetic) on time trend.
    H0: Slope = 0 (Parallel trends)
    """
    print(f"\n{'='*60}")
    print("TEST 1: DIFFERENCE IN SLOPES (Parallel Trends Test)")
    print(f"{'='*60}")
    
    y = data['Actual'] - data['Synthetic']
    X = np.arange(len(y))
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    slope = model.params[1]
    p_value = model.pvalues[1]
    ci = model.conf_int().iloc[1]
    
    print(f"Slope Coefficient: {slope:.5f}")
    print(f"P-value: {p_value:.4f}")
    print(f"95% CI: [{ci[0]:.5f}, {ci[1]:.5f}]")
    
    if p_value > 0.05:
        print("✓ H0 NOT REJECTED: Evidence supports parallel trends (slope not significantly different from 0)")
    else:
        print("✗ H0 REJECTED: Warning - possible pre-trend divergence found")
        
    return {
        'slope': slope,
        'p_value': p_value,
        'lower_ci': ci[0],
        'upper_ci': ci[1]
    }

def equivalence_test(data, threshold=1.0):
    """
    Test 2: Equivalence Test (TOST)
    Check if the mean difference is within a strict equivalence bound
    """
    print(f"\n{'='*60}")
    print("TEST 2: EQUIVALENCE TEST on Pre-intervention Gap")
    print(f"{'='*60}")
    
    gap = data['Actual'] - data['Synthetic']
    mean_gap = gap.mean()
    std_gap = gap.std()
    n = len(gap)
    
    # One-sided t-tests
    # H0: mean_gap <= -threshold OR mean_gap >= threshold
    # H1: -threshold < mean_gap < threshold
    
    t1 = (mean_gap - (-threshold)) / (std_gap / np.sqrt(n))
    p1 = 1 - stats.t.cdf(t1, df=n-1)
    
    t2 = (mean_gap - threshold) / (std_gap / np.sqrt(n))
    p2 = stats.t.cdf(t2, df=n-1)
    
    p_value = max(p1, p2)
    
    print(f"Mean Gap: {mean_gap:.4f}")
    print(f"Equivalence Threshold: ±{threshold} index points")
    print(f"P-value (TOST): {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"✓ EQUIVALENCE ESTABLISHED: Pre-trend gap is significantly within ±{threshold}")
    else:
        print(f"✗ EQUIVALENCE NOT ESTABLISHED: Cannot rule out gap > {threshold}")
        
    return {
        'mean_gap': mean_gap,
        'p_value': p_value
    }

def plot_pretrend_analysis(data):
    """Visual inspection of pre-trends with trend lines"""
    plt.figure(figsize=(10, 6))
    
    # Gap series
    gap = data['Actual'] - data['Synthetic']
    
    plt.plot(gap.index, gap, 'o-', color='gray', alpha=0.6, label='Pre-intervention Gap')
    
    # Calculated Trend Line
    X = np.arange(len(gap))
    model = sm.OLS(gap, sm.add_constant(X)).fit()
    pred = model.predict(sm.add_constant(X))
    
    plt.plot(gap.index, pred, color='red', linestyle='--', linewidth=2, label=f'Linear Trend (Slope={model.params[1]:.4f})')
    
    plt.axhline(0, color='black', linewidth=1)
    plt.fill_between(gap.index, -1, 1, color='green', alpha=0.1, label='Target Band (±1 pt)')
    
    plt.title('Pre-Trend Diagnostic: Divergence from Synthetic Control', fontsize=12)
    plt.ylabel('Gap (Actual - Synthetic)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    outfile = os.path.join(FIGURES_DIR, "pretrend_diagnostic.png")
    plt.savefig(outfile, dpi=300)
    print(f"\nPlot saved: {outfile}")

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
        
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    data = prepare_data(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE, START_DATE, PRE_PERIOD_END)
    
    results = {}
    results.update(diff_in_slopes_test(data))
    results.update(equivalence_test(data))
    
    plot_pretrend_analysis(data)
    
    # Save statistics
    res_df = pd.DataFrame([results])
    res_df.to_csv(os.path.join(RESULTS_DIR, "pretrend_test_statistics.csv"), index=False)
    print(f"Statistics saved: {os.path.join(RESULTS_DIR, 'pretrend_test_statistics.csv')}")

if __name__ == "__main__":
    main()
