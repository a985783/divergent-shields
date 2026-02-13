"""
Placebo Tests for Synthetic Control Method
Implements time placebo and permutation-based inference
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

# SCM Settings
TARGET_COUNTRY = 'ES'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'NL']
INTERVENTION_DATE = '2022-06-01'
START_DATE = '2019-01-01'
END_DATE = '2023-12-01'
VARIABLE = 'HICP_Total'  # Focus on headline inflation

def run_scm(df, target, donors, variable, start_date, intervention_date, end_date):
    """Run standard SCM - simplified for placebo tests"""
    pivot = df.pivot(index='date', columns='geo', values=variable)
    pivot = pivot.dropna()
    
    available_donors = [d for d in donors if d in pivot.columns]
    if target not in pivot.columns:
        return None
    
    mask_pre = (pivot.index >= start_date) & (pivot.index < intervention_date)
    mask_full = (pivot.index >= start_date) & (pivot.index <= end_date)
    
    # Pre-intervention data
    y_pre = pivot.loc[mask_pre, target]
    X_pre = pivot.loc[mask_pre, available_donors]
    
    # Optimization
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
    
    # Full data
    X_full = pivot.loc[mask_full, available_donors]
    y_full = pivot.loc[mask_full, target]
    synthetic_full = X_full.dot(weights)
    
    # Calculate gap
    gap = y_full - synthetic_full
    
    # Pre-intervention RMSPE
    rmspe_pre = np.sqrt(mean_squared_error(y_pre, X_pre.dot(weights)))
    
    return {
        'weights': dict(zip(available_donors, weights)),
        'rmspe_pre': rmspe_pre,
        'gap': gap,
        'actual': y_full,
        'synthetic': synthetic_full
    }

def time_placebo_test(df, placebo_date='2021-06-01'):
    """
    Time placebo test: Run SCM with fake intervention date
    """
    print(f"\n{'='*70}")
    print(f"TIME PLACEBO TEST")
    print(f"{'='*70}")
    print(f"Placebo intervention date: {placebo_date}")
    print(f"If effect is real, we should see NO effect before actual intervention")
    
    result = run_scm(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE, 
                    START_DATE, placebo_date, END_DATE)
    
    if result is None:
        print("Placebo test failed")
        return None
    
    # Calculate placebo effect
    placebo_gap = result['gap']
    placebo_post = placebo_gap[placebo_gap.index >= placebo_date]
    
    # Compare to actual effect
    actual_result = run_scm(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE,
                           START_DATE, INTERVENTION_DATE, END_DATE)
    
    if actual_result is None:
        print("Actual SCM failed")
        return None
    
    actual_gap = actual_result['gap']
    actual_post = actual_gap[actual_gap.index >= INTERVENTION_DATE]
    
    # Statistics
    placebo_effect = placebo_post.mean()
    actual_effect = actual_post.mean()
    
    print(f"\nPlacebo effect (pre-intervention): {placebo_effect:.4f}")
    print(f"Actual effect (post-intervention): {actual_effect:.4f}")
    print(f"Ratio (placebo/actual): {abs(placebo_effect/actual_effect):.3f}")
    
    # Plot comparison
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Placebo
    ax1 = axes[0]
    ax1.plot(placebo_gap.index, placebo_gap, color='blue', linewidth=2)
    ax1.axvline(pd.to_datetime(placebo_date), color='red', linestyle='--', 
                label=f'Placebo intervention ({placebo_date})')
    ax1.axvline(pd.to_datetime(INTERVENTION_DATE), color='gray', linestyle=':', 
                label=f'Actual intervention ({INTERVENTION_DATE})')
    ax1.axhline(0, color='black', linewidth=0.8)
    ax1.set_title(f'Time Placebo Test: Gap with Fake Intervention at {placebo_date}')
    ax1.set_ylabel('Gap (Actual - Synthetic)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add text
    ax1.text(0.02, 0.98, f"Mean post-placebo effect: {placebo_effect:.3f}\nPre-RMSPE: {result['rmspe_pre']:.3f}", 
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    # Plot 2: Actual for comparison
    ax2 = axes[1]
    ax2.plot(actual_gap.index, actual_gap, color='green', linewidth=2)
    ax2.axvline(pd.to_datetime(INTERVENTION_DATE), color='red', linestyle='--', 
                label=f'Actual intervention ({INTERVENTION_DATE})')
    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_title('Actual Treatment Effect (for comparison)')
    ax2.set_ylabel('Gap (Actual - Synthetic)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    ax2.text(0.02, 0.98, f"Mean post-intervention effect: {actual_effect:.3f}\nPre-RMSPE: {actual_result['rmspe_pre']:.3f}", 
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    
    # Save
    output_file = os.path.join(FIGURES_DIR, f"placebo_time_{placebo_date}_{VARIABLE}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Placebo plot saved: {output_file}")
    
    return {
        'placebo_effect': placebo_effect,
        'actual_effect': actual_effect,
        'ratio': abs(placebo_effect/actual_effect),
        'placebo_rmspe': result['rmspe_pre'],
        'actual_rmspe': actual_result['rmspe_pre']
    }

def permutation_test(df, n_permutations=100):
    """
    Permutation test: Randomly assign treatment to donor countries
    """
    print(f"\n{'='*70}")
    print(f"PERMUTATION TEST (Space Placebo)")
    print(f"{'='*70}")
    print(f"Running {n_permutations} permutations...")
    
    # Get actual treatment effect
    actual_result = run_scm(df, TARGET_COUNTRY, DONOR_POOL, VARIABLE,
                           START_DATE, INTERVENTION_DATE, END_DATE)
    
    if actual_result is None:
        print("Actual SCM failed")
        return None
    
    actual_gap = actual_result['gap']
    actual_post = actual_gap[actual_gap.index >= INTERVENTION_DATE]
    actual_effect = actual_post.mean()
    actual_rmspe = actual_result['rmspe_pre']
    
    print(f"Actual treatment effect: {actual_effect:.4f}")
    print(f"Actual pre-intervention RMSPE: {actual_rmspe:.4f}")
    
    # Run permutations: treat each donor as if it were the treated unit
    placebo_effects = []
    placebo_rmspes = []
    
    for i, donor in enumerate(DONOR_POOL):
        if donor == TARGET_COUNTRY:
            continue
            
        print(f"  Permutation {i+1}/{len(DONOR_POOL)-1}: Treating {donor} as treated unit")
        
        # Create new donor pool (exclude the "treated" donor)
        new_donors = [d for d in DONOR_POOL if d != donor]
        
        # Run SCM with this donor as "treated"
        placebo_result = run_scm(df, donor, new_donors, VARIABLE,
                                START_DATE, INTERVENTION_DATE, END_DATE)
        
        if placebo_result is None:
            continue
        
        # Calculate placebo effect
        placebo_gap = placebo_result['gap']
        placebo_post = placebo_gap[placebo_gap.index >= INTERVENTION_DATE]
        placebo_effect = placebo_post.mean()
        
        placebo_effects.append(placebo_effect)
        placebo_rmspes.append(placebo_result['rmspe_pre'])
    
    if len(placebo_effects) == 0:
        print("No successful permutations")
        return None
    
    # Calculate p-value
    # Two-sided test: proportion of placebo effects as extreme as actual
    extreme_effects = [abs(p) >= abs(actual_effect) for p in placebo_effects]
    p_value = np.mean(extreme_effects)
    
    print(f"\nPermutation test results:")
    print(f"Number of permutations: {len(placebo_effects)}")
    print(f"Placebo effects range: [{min(placebo_effects):.4f}, {max(placebo_effects):.4f}]")
    print(f"Actual effect: {actual_effect:.4f}")
    print(f"P-value: {p_value:.3f}")
    
    # Plot permutation distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Distribution of placebo effects
    ax1 = axes[0]
    ax1.hist(placebo_effects, bins=10, alpha=0.7, color='gray', edgecolor='black')
    ax1.axvline(actual_effect, color='red', linestyle='--', linewidth=3, 
                label=f'Actual effect ({actual_effect:.3f})')
    ax1.axvline(-actual_effect, color='red', linestyle='--', linewidth=3)
    ax1.axvline(0, color='black', linestyle='-', linewidth=1)
    ax1.set_xlabel('Placebo Treatment Effect')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Permutation Test: Distribution of Placebo Effects')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add p-value text
    ax1.text(0.05, 0.95, f"P-value: {p_value:.3f}\n{'Significant' if p_value < 0.05 else 'Not significant'} at 5% level", 
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightblue' if p_value < 0.05 else 'lightcoral', alpha=0.7))
    
    # Plot 2: Pre-intervention RMSPE comparison
    ax2 = axes[1]
    ax2.scatter(placebo_rmspes, [abs(p) for p in placebo_effects], 
                color='gray', alpha=0.7, s=60, label='Placebo tests')
    ax2.scatter(actual_rmspe, abs(actual_effect), 
                color='red', s=100, marker='*', label='Actual treatment', zorder=5)
    ax2.set_xlabel('Pre-intervention RMSPE')
    ax2.set_ylabel('Absolute Post-intervention Effect')
    ax2.set_title('RMSPE vs Treatment Effect')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_file = os.path.join(FIGURES_DIR, f"permutation_test_{VARIABLE}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Permutation test plot saved: {output_file}")
    
    return {
        'actual_effect': actual_effect,
        'placebo_effects': placebo_effects,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'actual_rmspe': actual_rmspe,
        'placebo_rmspes': placebo_rmspes
    }

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Run time placebo test
    print("Running time placebo test...")
    placebo_results = time_placebo_test(df, placebo_date='2021-06-01')
    
    # Run permutation test
    print("\nRunning permutation test...")
    perm_results = permutation_test(df, n_permutations=len(DONOR_POOL))
    
    # Save results
    if placebo_results:
        placebo_file = os.path.join(RESULTS_DIR, "placebo_time_results.csv")
        pd.DataFrame([placebo_results]).to_csv(placebo_file, index=False)
        print(f"\nPlacebo results saved: {placebo_file}")
    
    if perm_results:
        perm_file = os.path.join(RESULTS_DIR, "permutation_test_results.csv")
        perm_summary = {
            'actual_effect': perm_results['actual_effect'],
            'p_value': perm_results['p_value'],
            'significant': perm_results['significant'],
            'actual_rmspe': perm_results['actual_rmspe'],
            'n_permutations': len(perm_results['placebo_effects'])
        }
        pd.DataFrame([perm_summary]).to_csv(perm_file, index=False)
        print(f"Permutation results saved: {perm_file}")
        
        # Save all placebo effects
        placebo_effects_df = pd.DataFrame({
            'donor': [d for d in DONOR_POOL if d != TARGET_COUNTRY],
            'placebo_effect': perm_results['placebo_effects'],
            'placebo_rmspe': perm_results['placebo_rmspes']
        })
        placebo_effects_file = os.path.join(RESULTS_DIR, "placebo_effects_all.csv")
        placebo_effects_df.to_csv(placebo_effects_file, index=False)
        print(f"All placebo effects saved: {placebo_effects_file}")
    
    print(f"\n{'='*70}")
    print("All placebo tests completed!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
