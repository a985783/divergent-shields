
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Hardened Specification (Separated Shocks)
VARIABLES = ['HICP_Total', 'HICP_Core', 'IP_Total'] 
# Shocks:
# Global Shock: EUR-based Gas Price (to avoid double counting USD factor)
SHOCK_GLOBAL = 'DL_Gas_EUR'
SHOCK_FX = 'DL_XR_Local'
CONTROLS = ['EA_IP_Total'] # Proxy for Global/Regional Demand
HORIZONS = 12

def run_lp(df, country, dep_var, h):
    """
    Runs Local Projection for horizon h.
    Equation: y_{t+h} - y_{t-1} = alpha + beta * GlobalShock + phi * FXShock + ...
    LHS: Cumulative log change * 100 (Percentage change in level)
    """
    # Create LHS: Cumulative Change (Log Level)
    # y_{t+h} - y_{t-1}
    # df has variables as indices (e.g. 100, 105).
    # log(y).
    
    temp = df[['date', dep_var, SHOCK_GLOBAL, SHOCK_FX]].copy()
    temp['log_dep'] = np.log(temp[dep_var])
    temp['target'] = temp['log_dep'].shift(-h) - temp['log_dep'].shift(1)
    temp['target'] = temp['target'] * 100 # In Percent
    
    # Shocks are already DL (Diff Log * 100).
    # SHOCK_GLOBAL: Global Gas Price Change (%)
    # SHOCK_FX: Local Currency Depreciation (%)
    
    # Controls: Lags of Dep Var growth, Shocks growth?? 
    # Shocks are already growth rates. So Lags of shocks.
    
    dep_growth = temp['log_dep'].diff() * 100
    temp['lag_dep_1'] = dep_growth.shift(1)
    temp['lag_dep_2'] = dep_growth.shift(2)
    
    temp['lag_shock_global_1'] = temp[SHOCK_GLOBAL].shift(1)
    temp['lag_shock_fx_1'] = temp[SHOCK_FX].shift(1)
    
    # Global Demand Control
    if 'EA_IP_Total' in df.columns:
        control_series = df['EA_IP_Total']
        # Log diff?
        # EA IP is index.
        temp['control_ea_growth'] = np.log(control_series).diff() * 100
        temp['lag_control_ea_1'] = temp['control_ea_growth'].shift(1)
    
    temp = temp.dropna()
    
    if temp.empty:
        return None, None
        
    features = [SHOCK_GLOBAL, SHOCK_FX, 'lag_dep_1', 'lag_dep_2', 'lag_shock_global_1', 'lag_shock_fx_1']
    if 'lag_control_ea_1' in temp.columns:
        features.append('lag_control_ea_1')
        
    X = temp[features]
    X = sm.add_constant(X)
    y = temp['target']
    
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': h + 1})
    
    # Return Coefficients for Global and FX
    return {
        'global_beta': model.params[SHOCK_GLOBAL],
        'global_se': model.bse[SHOCK_GLOBAL],
        'fx_beta': model.params[SHOCK_FX],
        'fx_se': model.bse[SHOCK_FX]
    }

def main():
    if not os.path.exists(DATA_PATH):
        print("Data not found.")
        return

    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['geo', 'date'])
    
    # Ensure EA_IP is available (merged into all rows? or just check)
    # It should be in df.
    
    results = []
    
    for country in ['ES', 'PL']:
        sub_df = df[df['geo'] == country].copy()
        if sub_df.empty: continue
        
        print(f"Running Separated LP for {country}...")
        
        for var in VARIABLES:
            if var not in sub_df.columns: continue
            
            # Storage
            res_global = {'irf': [], 'lower': [], 'upper': []}
            res_fx = {'irf': [], 'lower': [], 'upper': []}
            
            for h in range(HORIZONS + 1):
                params_dict = run_lp(sub_df, country, var, h)
                if params_dict:
                    # Global
                    b_g = params_dict['global_beta']
                    se_g = params_dict['global_se']
                    res_global['irf'].append(b_g)
                    res_global['lower'].append(b_g - 1.96*se_g)
                    res_global['upper'].append(b_g + 1.96*se_g)
                    
                    # FX
                    b_f = params_dict['fx_beta']
                    se_f = params_dict['fx_se']
                    res_fx['irf'].append(b_f)
                    res_fx['lower'].append(b_f - 1.96*se_f)
                    res_fx['upper'].append(b_f + 1.96*se_f)
                else:
                    for d in [res_global, res_fx]:
                        d['irf'].append(0); d['lower'].append(0); d['upper'].append(0)
            
            # Plotting Logic (Two plots per variable: Global Impact, FX Impact)
            # 1. Global Shock Impact
            plt.figure(figsize=(8, 5))
            plt.plot(range(HORIZONS+1), res_global['irf'], label='Global Gas Shock', color='green')
            plt.fill_between(range(HORIZONS+1), res_global['lower'], res_global['upper'], color='green', alpha=0.15)
            plt.axhline(0, color='black', linewidth=0.5)
            plt.title(f'Response of {var} to Global Gas Price Shock - {country}')
            plt.ylabel('% Change in Price Level')
            plt.xlabel('Months')
            plt.savefig(os.path.join(FIGURES_DIR, f'IRF_{country}_{var}_GlobalGas.png'))
            plt.close()
            
            # 2. FX Shock Impact (Only relevant if FX volatile, but we plot for both)
            plt.figure(figsize=(8, 5))
            plt.plot(range(HORIZONS+1), res_fx['irf'], label='FX Depreciation Shock', color='purple')
            plt.fill_between(range(HORIZONS+1), res_fx['lower'], res_fx['upper'], color='purple', alpha=0.15)
            plt.axhline(0, color='black', linewidth=0.5)
            plt.title(f'Response of {var} to FX Depreciation - {country}')
            plt.ylabel('% Change in Price Level')
            plt.xlabel('Months')
            plt.savefig(os.path.join(FIGURES_DIR, f'IRF_{country}_{var}_FX.png'))
            plt.close()
            
    print("Separated LP Analysis Complete.")

if __name__ == "__main__":
    main()
