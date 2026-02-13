"""
Fiscal Cost Estimation and Sacrifice Ratio Analysis
Calculates the "Fiscal Sacrifice Ratio" for Spain's Iberian Mechanism
and compares it with Poland's output loss.
"""


# Get project root directory dynamically
import os

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
SCM_RESULTS_PATH = os.path.join(PROJECT_ROOT, "paper", "tables", "scm_enhanced_ES_HICP_Total.csv")
LP_RESULTS_PATH = os.path.join(PROJECT_ROOT, "paper", "tables", "lp_enhanced_PL.csv")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Intervention Parameters
START_DATE = '2022-06-15'
END_DATE = '2023-12-31'
INTERVENTION_START = '2022-06-01'

# Economic Parameters (Source: Eurostat 2022)
SPAIN_GDP_2022_EUR = 1.346e12  # 1.346 Trillion Euros
EST_MONTHLY_GAS_GEN_TWH = 6.0  # TWh per month (Gas for Power)

def load_inflation_reduction():
    """Load SCM results to get the actual inflation reduction (gap)"""
    if not os.path.exists(SCM_RESULTS_PATH):
        print(f"Warning: SCM results not found at {SCM_RESULTS_PATH}. Using default.")
        return 1.74 # Default from previous run
        
    df = pd.read_csv(SCM_RESULTS_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter post-intervention
    mask = df['date'] >= INTERVENTION_START
    post_df = df.loc[mask]
    
    # Calculate average gap in YoY inflation
    # gap_yoy is Actual - Synthetic. 
    # If the policy worked, Actual < Synthetic, so Gap is negative.
    # We want the magnitude of reduction (positive value).
    
    avg_reduction = -post_df['gap_yoy'].mean()
    print(f"Loaded SCM Results: Average Inflation Reduction = {avg_reduction:.2f} pp")
    return avg_reduction

def calculate_fiscal_cost():
    """Calculate total fiscal cost of the cap"""
    # Simulate price path (approximation based on TTF history)
    ttf_prices = {
        '2022-06-01': 100, '2022-07-01': 170, '2022-08-01': 230, '2022-09-01': 190,
        '2022-10-01': 130, '2022-11-01': 110, '2022-12-01': 120,
        '2023-01-01': 70,  '2023-02-01': 60,  '2023-03-01': 50,  '2023-04-01': 45,
        '2023-05-01': 35,  '2023-06-01': 35,  '2023-07-01': 30,  '2023-08-01': 35,
        '2023-09-01': 40,  '2023-10-01': 45,  '2023-11-01': 50,  '2023-12-01': 40
    }
    
    dates = pd.to_datetime(list(ttf_prices.keys()))
    prices = list(ttf_prices.values())
    df = pd.DataFrame({'date': dates, 'market_price': prices})
    
    # Cap schedule: 40 EUR for 6m, then +5/m
    df['cap_price'] = 40.0
    mask_step = df['date'] >= '2023-01-01'
    # Simplified step up for estimation
    df.loc[mask_step, 'cap_price'] = 55.0 # Average cap in 2023
    
    df['subsidy'] = (df['market_price'] - df['cap_price']).clip(lower=0)
    
    # Total cost
    monthly_vol_mwh = EST_MONTHLY_GAS_GEN_TWH * 1e6
    df['cost'] = df['subsidy'] * monthly_vol_mwh
    
    total_cost = df['cost'].sum()
    return total_cost

def main():
    print(f"\n{'='*70}")
    print("COST-BENEFIT ANALYSIS: SACRIFICE RATIOS")
    print(f"{'='*70}")
    
    # 1. Spain Analysis
    inflation_reduction_pp = load_inflation_reduction()
    # Updated to match paper's range estimate approach
    # Range: €5-8 Billion (based on government disclosures)
    # Mid-point: €6.5 Billion (~0.5% GDP)
    
    fiscal_cost_low_bn = 5.0
    fiscal_cost_high_bn = 8.0
    fiscal_cost_mid_bn = 6.5
    
    fiscal_cost_pct_gdp_mid = (fiscal_cost_mid_bn * 1e9 / SPAIN_GDP_2022_EUR) * 100
    
    # Fiscal Sacrifice Ratio = (% GDP Cost) / (Inflation Reduction pp)
    fiscal_sacrifice = fiscal_cost_pct_gdp_mid / inflation_reduction_pp
    
    print("\n[SPAIN] Structural Intervention (Range Estimate):")
    print(f"  Total Fiscal Cost: €{fiscal_cost_low_bn}-{fiscal_cost_high_bn} Bn")
    print(f"  Fiscal Cost (Mid-point % GDP): {fiscal_cost_pct_gdp_mid:.2f}%")
    print(f"  Inflation Reduction: {inflation_reduction_pp:.2f} pp")
    print(f"  > FISCAL SACRIFICE RATIO: {fiscal_sacrifice:.3f} (% GDP per 1 pp inflation)")
    
    # 2. Poland Analysis (Counterfactual Comparison)
    pl_output_loss_pct = 2.59 # From LP results
    
    print("\n[POLAND] Monetary Orthodoxy (Reference):")
    print(f"  Industrial Production Loss (Max LP effect): {pl_output_loss_pct:.2f}%")
    print("  > OUTPUT SACRIFICE: High (Recessionary Adjustment)")
    
    # Save Summary Table
    summary = pd.DataFrame({
        'Metric': ['Fiscal Cost (Bn EUR)', 'Fiscal Cost (% GDP)',
                   'Inflation Reduction (pp)', 'Fiscal Sacrifice Ratio'],
        'Value': [fiscal_cost_mid_bn, fiscal_cost_pct_gdp_mid,
                  inflation_reduction_pp, fiscal_sacrifice]
    })
    
    output_file = os.path.join(RESULTS_DIR, "cost_benefit_sacrifice_ratio.csv")
    summary.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
