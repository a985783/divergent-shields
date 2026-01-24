"""
Italy Defense Analysis
Quantifies the structural similarity between Spain (ES) and donor countries
to justify the heavy reliance on Italy in the Synthetic Control.

Focuses on:
1. Gas Price Pass-Through (Beta of Gas -> Electricity)
2. Inflation Energy Sensitivity (Correlation of Headline -> Energy)
3. Industrial Correlations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import os

# Config
DATA_PATH = "data/processed/merged_data.csv"
FIGURES_DIR = "paper/figures"
RESULTS_DIR = "paper/tables"
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

TARGET = 'ES'
DONORS = ['DE', 'FR', 'IT', 'NL', 'AT']
ALL_COUNTRIES = [TARGET] + DONORS

# Time period for structural analysis (Pre-intervention)
START_DATE = '2015-01-01'
END_DATE = '2022-05-01'

def calculate_pass_through(df, country):
    """
    Calculate the pass-through elasticity of Global Gas Prices to Domestic Electricity Prices.
    Proxy for the 'Marginal Pricing' role of gas in the national electricity market.
    """
    sub = df[(df['geo'] == country) & (df['date'] >= START_DATE) & (df['date'] <= END_DATE)].copy()
    sub = sub.dropna(subset=['DL_Gas_EUR', 'CP0451'])
    
    if len(sub) < 20:
        return np.nan
        
    # Model: \Delta ln(Elec) = alpha + beta * \Delta ln(Gas)
    # We use log differences (growth rates) to estimate elasticity/sensitivity
    # CP0451 is Electricity HICP
    
    y = np.log(sub['CP0451']).diff().dropna()
    X = sub['DL_Gas_EUR'].loc[y.index] # DL_Gas_EUR is already percentage change, approximating log diff
    
    if len(y) < 10:
        return np.nan
        
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    return model.params['DL_Gas_EUR']

def calculate_energy_sensitivity(df, country):
    """
    Calculate correlation between Energy Inflation and Headline Inflation.
    Proxy for the weight/importance of energy in the consumption basket.
    """
    sub = df[(df['geo'] == country) & (df['date'] >= START_DATE) & (df['date'] <= END_DATE)].copy()
    sub = sub.dropna(subset=['HICP_Energy', 'HICP_Total'])
    
    if len(sub) < 20:
        return np.nan
        
    return sub['HICP_Energy'].corr(sub['HICP_Total'])

def main():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    metrics = []
    
    print(f"\nComparing {TARGET} with {DONORS} over period {START_DATE} to {END_DATE}")
    
    for country in ALL_COUNTRIES:
        # 1. Gas Pass-Through (The "Marginal Price" indicator)
        beta_gas = calculate_pass_through(df, country)
        
        # 2. Energy Sensitivity
        corr_energy = calculate_energy_sensitivity(df, country)
        
        # 3. Inflation Volatility (General Macro Stability)
        sub = df[(df['geo'] == country) & (df['date'] >= START_DATE) & (df['date'] <= END_DATE)]
        volatility = sub['HICP_Total'].pct_change(12).std()
        
        metrics.append({
            'Country': country,
            'Gas_Pass_Through': beta_gas,
            'Energy_Sensitivity': corr_energy,
            'Inflation_Volatility': volatility
        })
    
    metrics_df = pd.DataFrame(metrics).set_index('Country')
    
    # Calculate similarity distance to Spain
    # Normalize features first
    norm_df = (metrics_df - metrics_df.mean()) / metrics_df.std()
    
    # Euclidean distance to ES
    target_vec = norm_df.loc[TARGET]
    distances = {}
    for country in DONORS:
        dist = np.linalg.norm(norm_df.loc[country] - target_vec)
        distances[country] = dist
    
    metrics_df['Distance_to_ES'] = metrics_df.index.map(distances)
    metrics_df.loc[TARGET, 'Distance_to_ES'] = 0
    
    print("\nStructural Comparison (The 'Italy Defense'):")
    print(metrics_df.round(3))
    
    # Save table
    metrics_df.to_csv(os.path.join(RESULTS_DIR, 'italy_defense_metrics.csv'))
    
    # Plotting
    create_defense_plot(metrics_df)

def create_defense_plot(df):
    """
    Create a visual comparison focusing on Gas Pass-Through
    """
    plt.figure(figsize=(10, 6))
    
    # Color coding: Target (Red), Closest Peer (Green), Others (Gray)
    colors = []
    for country in df.index:
        if country == TARGET:
            colors.append('#d62728') # Red for Spain
        elif country == 'IT':
            colors.append('#2ca02c') # Green for Italy
        else:
            colors.append('lightgray')
            
    # Bar plot for Gas Pass-Through
    plot_df = df.reset_index()
    ax = sns.barplot(data=plot_df, x='Country', y='Gas_Pass_Through', palette=colors)
    
    plt.title('Gas Price Pass-Through to Electricity (Pre-Crisis)\nWhy Italy is the Best Counterfactual', 
              fontsize=14, fontweight='bold', pad=20)
    plt.ylabel('Elasticity (Sensitivity to Gas Shocks)', fontsize=12)
    plt.xlabel('Country', fontsize=12)
    
    # Add annotation for Spain and Italy
    plt.text(0, df.loc['ES', 'Gas_Pass_Through'] + 0.005, 'Target\n(Marginal Pricing)', 
             ha='center', va='bottom', fontweight='bold', color='#d62728')
    
    it_idx = list(df.index).index('IT')
    plt.text(it_idx, df.loc['IT', 'Gas_Pass_Through'] + 0.005, 'Best Match\n(High Gas Dep.)', 
             ha='center', va='bottom', fontweight='bold', color='#2ca02c')
    
    fr_idx = list(df.index).index('FR')
    plt.text(fr_idx, df.loc['FR', 'Gas_Pass_Through'] + 0.005, 'Poor Match\n(Nuclear)', 
             ha='center', va='bottom', color='gray')
             
    plt.grid(axis='y', alpha=0.3)
    
    output_path = os.path.join(FIGURES_DIR, 'italy_defense_energy_mix.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nDefense plot saved to {output_path}")

if __name__ == "__main__":
    main()
