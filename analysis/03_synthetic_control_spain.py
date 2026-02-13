
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.utils.validation import check_X_y
from scipy.optimize import minimize

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Synthetic Control Settings
TARGET_COUNTRY = 'ES'
DONOR_POOL = ['DE', 'FR', 'IT', 'AT', 'PT', 'NL']
TARGET_VAR = 'HICP_Total' # Headline Inflation
START_DATE = '2019-01-01'
INTERVENTION_DATE = '2022-06-01' # Iberian Mechanism Implementation
END_DATE = '2024-12-01'

def synthetic_control(df, target, donors, variable, start_date, intervention_date, end_date):
    """
    Implements a simple Synthetic Control Method using constrained Linear Regression (Non-negative weights summing to 1 would be ideal, 
    but OLS/Ridge on pre-trend is a robust approximation for "Synthetic" construction in many contexts if donors are well-chosen).
    
    For strict SCM (Abadie et al), we need to minimize distance of pre-intervention characteristics.
    Here we minimize pre-intervention prediction error of the outcome variable (Inflation).
    """
    
    # 1. Prepare Data
    pivot = df.pivot(index='date', columns='geo', values=variable)
    pivot = pivot.dropna()
    
    # Check availability
    available_donors = [d for d in donors if d in pivot.columns]
    if target not in pivot.columns:
        print(f"Target {target} not in data.")
        return
    
    print(f"Comparison: {target} vs {available_donors}")
    
    # Subset time
    mask_pre = (pivot.index >= start_date) & (pivot.index < intervention_date)
    mask_post = (pivot.index >= intervention_date) & (pivot.index <= end_date)
    
    # X (Donors) and y (Target)
    X_pre = pivot.loc[mask_pre, available_donors]
    y_pre = pivot.loc[mask_pre, target]
    
    X_full = pivot.loc[(pivot.index >= start_date) & (pivot.index <= end_date), available_donors]
    y_full = pivot.loc[(pivot.index >= start_date) & (pivot.index <= end_date), target]
    
    # 2. Estimate Weights
    # We want w such that y_pre ~ X_pre * w
    # Constraint: sum(w) = 1, w >= 0.
    # We can use scipy.optimize for this.
    from scipy.optimize import minimize
    
    def loss(w):
        return np.sum((y_pre - X_pre.dot(w))**2)
    
    def constraint_sum(w):
        return np.sum(w) - 1.0
    
    n_donors = len(available_donors)
    w0 = np.ones(n_donors) / n_donors
    bounds = [(0, 1) for _ in range(n_donors)]
    constraints = [{'type': 'eq', 'fun': constraint_sum}]
    
    res = minimize(loss, w0, bounds=bounds, constraints=constraints)
    weights = res.x
    
    print("Synthetic Weights:")
    for d, w in zip(available_donors, weights):
        print(f"  {d}: {w:.3f}")
        
    # 3. Construct Synthetic Control
    synthetic = X_full.dot(weights)
    
    # 4. Plot
    plt.figure(figsize=(10, 6))
    plt.plot(y_full.index, y_full, label=f'Actual Spain ({variable})', color='red', linewidth=2.5)
    plt.plot(synthetic.index, synthetic, label='Synthetic Spain (Counterfactual)', color='black', linestyle='--', linewidth=2)
    
    # Add vertical line for intervention
    plt.axvline(pd.to_datetime(intervention_date), color='grey', linestyle=':', label='Iberian Mechanism (June 2022)')
    
    # Shade the difference
    plt.fill_between(y_full.index, y_full, synthetic, where=(y_full < synthetic), color='green', alpha=0.1, label='Inflation Reduction')
    plt.fill_between(y_full.index, y_full, synthetic, where=(y_full > synthetic), color='red', alpha=0.1)
    
    plt.title(f'The "Iberian Shield": Actual vs. Synthetic Spain Inflation\n(Variable: {variable})')
    plt.ylabel('Index Level (2015=100)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    out_path = os.path.join(FIGURES_DIR, f"SCM_{TARGET_COUNTRY}_{variable}.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved SCM plot to {out_path}")
    
    # Calculate Gap
    gap = y_full - synthetic
    gap_post = gap[gap.index >= intervention_date]
    mean_gap = gap_post.mean()
    print(f"Average Post-Intervention Gap (Index Points): {mean_gap:.2f}")
    
    # Plot YoY Results
    y_full_yoy = y_full.pct_change(12) * 100
    synthetic_yoy = synthetic.pct_change(12) * 100
    
    plt.figure(figsize=(10, 6))
    plt.plot(y_full_yoy.index, y_full_yoy, label=f'Actual Spain {variable} (%)', color='red', linewidth=2.5)
    plt.plot(synthetic_yoy.index, synthetic_yoy, label=f'Synthetic Spain {variable} (%)', color='black', linestyle='--', linewidth=2)
    
    plt.axvline(pd.to_datetime(intervention_date), color='grey', linestyle=':', label='Intervention')
    plt.title(f'{variable} Inflation: Actual vs. Synthetic Spain')
    plt.ylabel('YoY % Change')
    plt.legend()
    plt.grid(True)
    
    out_path_yoy = os.path.join(FIGURES_DIR, f"SCM_{TARGET_COUNTRY}_{variable}_YoY.png")
    plt.savefig(out_path_yoy, dpi=300)
    plt.close()

def run_leave_one_out(df, target, donors, variable, start_date, intervention_date, end_date):
    """
    Runs SCM multiple times, excluding one donor at a time to check robustness.
    """
    print(f"\n--- Running Leave-One-Out Robustness for {variable} ---")
    
    # 1. Main Synthetic Control (Reference)
    # We need to re-calculate the main synthetic control to have the baseline
    # Ideally reuse code, but for speed we just copy-paste the core logic or refactor.
    # For now, let's just plot the variations.
    
    variations = []
    
    for exclude_country in donors:
        # Create new donor pool
        sub_pool = [d for d in donors if d != exclude_country]
        if not sub_pool: continue
        
        # Prepare Data
        pivoted = df.pivot(index='date', columns='geo', values=variable)
        if target not in pivoted.columns: continue
        
        # Check donors availability
        available_donors = [c for c in sub_pool if c in pivoted.columns]
        
        # Drop NaN
        data_clean = pivoted[[target] + available_donors].dropna()
        if data_clean.empty: continue
        
        # Split Data
        pre_intervention = data_clean[data_clean.index < intervention_date]
        if pre_intervention.empty: continue
        
        y_pre = pre_intervention[target].values
        X_pre = pre_intervention[available_donors].values
        
        # Optimize Weights
        def loss(w): return np.sum((y_pre - X_pre.dot(w))**2)
        def constraint_sum(w): return np.sum(w) - 1.0
        
        w0 = np.ones(len(available_donors)) / len(available_donors)
        bounds = [(0, 1) for _ in range(len(available_donors))]
        constraints = [{'type': 'eq', 'fun': constraint_sum}]
        
        try:
            res = minimize(loss, w0, bounds=bounds, constraints=constraints)
            weights = res.x
            
            # Construct Synthetic
            X_full = data_clean[available_donors].values
            synthetic = X_full.dot(weights)
            synthetic_series = pd.Series(synthetic, index=data_clean.index)
            
            variations.append((exclude_country, synthetic_series))
        except Exception as e:
            print(f"Failed LOO for {exclude_country}: {e}")
            
    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Plot Real Data
    # Get Real Data again (hacky but safe)
    pivoted_full = df.pivot(index='date', columns='geo', values=variable)
    y_real = pivoted_full[target].dropna()
    plt.plot(y_real.index, y_real, label='Actual Spain', color='red', linewidth=3, zorder=10)
    
    # Plot Variations
    for country, series in variations:
        plt.plot(series.index, series, color='grey', alpha=0.5, linewidth=1, label='_nolegend_')
        
    plt.axvline(pd.to_datetime(intervention_date), color='blue', linestyle=':', label='Intervention')
    plt.title(f'Robustness Check: Leave-One-Out SCM ({variable})')
    plt.ylabel('Index Level')
    plt.legend(['Actual Spain', 'Leave-One-Out Controls'])
    plt.grid(True)
    
    out_path = os.path.join(FIGURES_DIR, f"SCM_{target}_{variable}_LOO.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved LOO plot to {out_path}")

    
    print(f"Saved LOO plot to {out_path}")

def main():
    if not os.path.exists(DATA_PATH):
        print("Data not found.")
        return
        
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Run SCM for multiple variables
    targets = [
        ('HICP_Total', 'Headline Inflation'), 
        ('CP0451', 'Electricity Prices'),
        ('HICP_Energy', 'Energy Inflation')
    ]
    
    for var_code, var_name in targets:
        print(f"\n--- Running SCM for {var_name} ({var_code}) ---")
        synthetic_control(df, TARGET_COUNTRY, DONOR_POOL, var_code, START_DATE, INTERVENTION_DATE, END_DATE)
        run_leave_one_out(df, TARGET_COUNTRY, DONOR_POOL, var_code, START_DATE, INTERVENTION_DATE, END_DATE)

if __name__ == "__main__":
    main()
