"""
Robustness Checks for Synthetic Control Method
Tests different donor pools and time periods
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

# Base settings
TARGET_COUNTRY = 'ES'
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'
VARIABLE = 'HICP_Total'

def run_scm_basic(df, target, donors, variable, start_date, intervention_date, end_date):
    """Simplified SCM for robustness checks"""
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
    
    gap_post = gap[gap.index >= intervention_date]
    ate = gap_post.mean()
    
    return {
        'weights': dict(zip(available_donors, weights)),
        'rmspe_pre': rmspe_pre,
        'ate': ate,
        'gap': gap,
        'donors_used': available_donors
    }

def test_donor_pools(df):
    """Test different donor pool specifications"""
    print(f"\n{'='*70}")
    print("ROBUSTNESS: DIFFERENT DONOR POOLS")
    print(f"{'='*70}")
    
    donor_pools = {
        'Baseline': ['DE', 'FR', 'IT', 'AT', 'NL'],
        'Exclude France': ['DE', 'IT', 'AT', 'NL'],  # France has nuclear special case
        'Exclude Italy': ['DE', 'FR', 'AT', 'NL'],  # Italy has debt concerns
        'Core Eurozone': ['DE', 'FR', 'NL'],  # Only largest economies
        'Southern Europe': ['IT', 'FR', 'PT'],  # Mediterranean countries
        'Expanded': ['DE', 'FR', 'IT', 'AT', 'NL', 'PT', 'BE', 'IE'], # Broadest pool
    }
    
    results = {}
    
    for name, donors in donor_pools.items():
        print(f"\nTesting donor pool: {name}")
        print(f"Donors: {donors}")
        
        result = run_scm_basic(df, TARGET_COUNTRY, donors, VARIABLE, 
                              START_DATE, INTERVENTION_DATE, END_DATE)
        
        if result:
            results[name] = result
            print(f"  RMSPE: {result['rmspe_pre']:.4f}")
            print(f"  ATE: {result['ate']:.4f}")
            print(f"  Effective donors: {len(result['donors_used'])}")
            print(f"  Weights: {result['weights']}")
        else:
            print(f"  Failed to converge")
    
    # Create comparison table
    if results:
        comparison = []
        for name, result in results.items():
            comparison.append({
                'Donor Pool': name,
                'RMSPE': result['rmspe_pre'],
                'ATE': result['ate'],
                'Donors Used': len(result['donors_used'])
            })
        
        comparison_df = pd.DataFrame(comparison)
        print(f"\n{'='*70}")
        print("DONOR POOL COMPARISON")
        print(f"{'='*70}")
        print(comparison_df.to_string(index=False))
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, "robustness_donor_pools.csv")
        comparison_df.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")
        
        # Plot comparison
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # RMSPE comparison
        ax1 = axes[0]
        bars = ax1.bar(comparison_df['Donor Pool'], comparison_df['RMSPE'], 
                       color='steelblue', alpha=0.7)
        ax1.set_ylabel('Pre-intervention RMSPE')
        ax1.set_title('Model Fit by Donor Pool')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add values on bars
        for bar, value in zip(bars, comparison_df['RMSPE']):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                     f'{value:.3f}', ha='center', va='bottom')
        
        # ATE comparison
        ax2 = axes[1]
        bars = ax2.bar(comparison_df['Donor Pool'], comparison_df['ATE'], 
                       color='darkgreen', alpha=0.7)
        ax2.axhline(0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_ylabel('Average Treatment Effect')
        ax2.set_title('Treatment Effect by Donor Pool')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add values on bars
        for bar, value in zip(bars, comparison_df['ATE']):
            ax2.text(bar.get_x() + bar.get_width()/2, 
                     bar.get_height() + 0.05 if value >= 0 else bar.get_height() - 0.15,
                     f'{value:.3f}', ha='center', 
                     va='bottom' if value >= 0 else 'top')
        
        plt.tight_layout()
        
        # Save plot
        plot_file = os.path.join(FIGURES_DIR, "robustness_donor_pools.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved: {plot_file}")
        
        return comparison_df
    else:
        print("No successful results")
        return None

def test_time_periods(df):
    """Test different pre-intervention periods"""
    print(f"\n{'='*70}")
    print("ROBUSTNESS: DIFFERENT TIME PERIODS")
    print(f"{'='*70}")
    
    time_periods = {
        'Baseline (2019-2022)': ('2019-01-01', '2022-06-01'),
        'Extended (2018-2022)': ('2018-01-01', '2022-06-01'),
        'Short (2020-2022)': ('2020-01-01', '2022-06-01'),
        'Pre-COVID (2019-2020)': ('2019-01-01', '2020-01-01'),
        'COVID Period (2020-2022)': ('2020-01-01', '2022-06-01'),
    }
    
    results = {}
    baseline_ate = None
    
    for name, (start, intervention) in time_periods.items():
        print(f"\nTesting period: {name}")
        print(f"Start: {start}, Intervention: {intervention}")
        
        result = run_scm_basic(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE, 
                              start, intervention, END_DATE)
        
        if result:
            results[name] = result
            print(f"  RMSPE: {result['rmspe_pre']:.4f}")
            print(f"  ATE: {result['ate']:.4f}")
            
            # Store baseline for comparison
            if name == 'Baseline (2019-2022)':
                baseline_ate = result['ate']
        else:
            print(f"  Failed to converge")
    
    # Create comparison table
    if results:
        comparison = []
        for name, result in results.items():
            ate_change = None
            if baseline_ate and name != 'Baseline (2019-2022)':
                ate_change = (result['ate'] - baseline_ate) / abs(baseline_ate) * 100
            
            comparison.append({
                'Time Period': name,
                'Start Date': time_periods[name][0],
                'RMSPE': result['rmspe_pre'],
                'ATE': result['ate'],
                'Change from Baseline (%)': ate_change
            })
        
        comparison_df = pd.DataFrame(comparison)
        print(f"\n{'='*70}")
        print("TIME PERIOD COMPARISON")
        print(f"{'='*70}")
        print(comparison_df.to_string(index=False))
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, "robustness_time_periods.csv")
        comparison_df.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")
        
        return comparison_df
    else:
        print("No successful results")
        return None

def test_outcome_variables(df):
    """Test different outcome variables"""
    print(f"\n{'='*70}")
    print("ROBUSTNESS: DIFFERENT OUTCOME VARIABLES")
    print(f"{'='*70}")
    
    variables = {
        'Headline Inflation': 'HICP_Total',
        'Core Inflation': 'HICP_Core',
        'Energy Inflation': 'HICP_Energy',
        'Electricity Prices': 'CP0451'
    }
    
    results = {}
    
    for name, var in variables.items():
        if var not in df.columns:
            print(f"\nSkipping {name}: {var} not in data")
            continue
        
        print(f"\nTesting variable: {name} ({var})")
        
        result = run_scm_basic(df, TARGET_COUNTRY, DONOR_POOL, var, 
                              START_DATE, INTERVENTION_DATE, END_DATE)
        
        if result:
            results[name] = result
            print(f"  RMSPE: {result['rmspe_pre']:.4f}")
            print(f"  ATE: {result['ate']:.4f}")
        else:
            print(f"  Failed to converge")
    
    # Create comparison table
    if results:
        comparison = []
        for name, result in results.items():
            var_key = [k for k, v in variables.items() if v == [v for v in variables.values() if v in df.columns and v in str(result)][0]][0]
            
            comparison.append({
                'Outcome Variable': name,
                'RMSPE': result['rmspe_pre'],
                'ATE': result['ate'],
                'Donors Used': len(result['donors_used'])
            })
        
        comparison_df = pd.DataFrame(comparison)
        print(f"\n{'='*70}")
        print("OUTCOME VARIABLE COMPARISON")
        print(f"{'='*70}")
        print(comparison_df.to_string(index=False))
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, "robustness_outcome_variables.csv")
        comparison_df.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")
        
        return comparison_df
    else:
        print("No successful results")
        return None

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    print("Running comprehensive robustness checks...")
    
    # Test 1: Different donor pools
    donor_results = test_donor_pools(df)
    
    # Test 2: Different time periods
    time_results = test_time_periods(df)
    
    # Test 3: Different outcome variables
    outcome_results = test_outcome_variables(df)
    
    # Create summary
    print(f"\n{'='*70}")
    print("ROBUSTNESS CHECK SUMMARY")
    print(f"{'='*70}")
    
    if donor_results is not None:
        print(f"✓ Donor pool tests: {len(donor_results)} specifications")
    if time_results is not None:
        print(f"✓ Time period tests: {len(time_results)} specifications")
    if outcome_results is not None:
        print(f"✓ Outcome variable tests: {len(outcome_results)} specifications")
    
    print(f"\nAll robustness checks completed!")
    print(f"Results saved in: {RESULTS_DIR}")
    print(f"Figures saved in: {FIGURES_DIR}")

if __name__ == "__main__":
    main()
