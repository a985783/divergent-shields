"""
Enhanced Local Projections with Country-Specific Specifications
Implements separate models for Spain (EUR) and Poland (PLN) with proper controls
"""


# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Model specifications by country
COUNTRY_SPECS = {
    'ES': {
        'name': 'Spain',
        'has_fx': False,  # EUR country, no independent FX shock
        'shock_vars': ['DL_Gas_EUR'],  # Only global shock
        'control_vars': ['lag_dep_1', 'lag_dep_2', 'lag_shock_global_1', 'EA_IP_Total'],
        'description': 'Spain (Eurozone): Only global gas shock, no FX'
    },
    'PL': {
        'name': 'Poland',
        'has_fx': True,   # PLN country, has FX shock
        'shock_vars': ['DL_Gas_EUR', 'DL_XR_Local'],  # Global + FX shock
        'interaction': True, # Enable interaction terms
        'control_vars': ['lag_dep_1', 'lag_dep_2', 'lag_shock_global_1', 'lag_shock_fx_1', 'EA_IP_Total'],
        'description': 'Poland (Inflation Targeter): Global gas + FX shocks with Interaction'
    }
}

# Variables to analyze
VARIABLES = ['HICP_Total', 'HICP_Core', 'IP_Total']
HORIZONS = 12

def run_enhanced_lp(df, country, dep_var, horizon, country_spec):
    """
    Run enhanced local projection for a specific country and horizon
    Returns detailed results with standard errors and significance
    """
    sub_df = df[df['geo'] == country].copy()
    if sub_df.empty:
        return None
    
    # Prepare data
    temp = sub_df[['date', dep_var] + country_spec['shock_vars']].copy()
    
    # Log levels for LHS
    temp['log_dep'] = np.log(temp[dep_var])
    temp['target'] = (temp['log_dep'].shift(-horizon) - temp['log_dep'].shift(1)) * 100
    
    # Shocks (already in percentage)
    for shock in country_spec['shock_vars']:
        temp[shock] = temp[shock]

    # Add Interaction Term if specified
    if country_spec.get('interaction', False) and len(country_spec['shock_vars']) >= 2:
        # Assuming first two shocks are Gas and FX
        s1 = country_spec['shock_vars'][0] # DL_Gas_EUR
        s2 = country_spec['shock_vars'][1] # DL_XR_Local
        interaction_name = 'Interaction_Gas_FX'
        temp[interaction_name] = temp[s1] * temp[s2]
        # Add to features list for regression later
        # We need to manage this dynamically in the regression step

    
    # Lagged dependent variable growth
    dep_growth = temp['log_dep'].diff() * 100
    temp['lag_dep_1'] = dep_growth.shift(1)
    temp['lag_dep_2'] = dep_growth.shift(2)
    
    # Lagged shocks
    for shock in country_spec['shock_vars']:
        temp[f'lag_{shock}_1'] = temp[shock].shift(1)
    
    # Controls
    if 'EA_IP_Total' in sub_df.columns:
        temp['EA_IP_Total'] = sub_df['EA_IP_Total'].values
    
    # Drop NA
    temp = temp.dropna()
    
    if temp.empty or len(temp) < 20:
        return None
    
    # Prepare regression
    features = country_spec['shock_vars'] + country_spec['control_vars']
    
    # Add interaction to features if present
    if 'Interaction_Gas_FX' in temp.columns:
        features = country_spec['shock_vars'] + ['Interaction_Gas_FX'] + country_spec['control_vars']

    
    # Remove features that don't exist
    features = [f for f in features if f in temp.columns]
    
    X = temp[features]
    X = sm.add_constant(X)
    y = temp['target']
    
    # Fit model with HAC standard errors
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': horizon + 1})
    
    # Extract results
    results = {
        'horizon': horizon,
        'n_obs': len(temp),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'f_statistic': model.fvalue,
        'f_pvalue': model.f_pvalue
    }
    
    # Shock-specific results (including interaction)
    reg_vars = country_spec['shock_vars']
    if 'Interaction_Gas_FX' in temp.columns:
        reg_vars = reg_vars + ['Interaction_Gas_FX']

    for shock in reg_vars:
        if shock in model.params.index:
            coef = model.params[shock]
            se = model.bse[shock]
            t_stat = model.tvalues[shock]
            p_value = model.pvalues[shock]
            
            # Confidence intervals
            ci_lower = coef - 1.96 * se
            ci_upper = coef + 1.96 * se
            
            results.update({
                f'{shock}_coef': coef,
                f'{shock}_se': se,
                f'{shock}_tstat': t_stat,
                f'{shock}_pvalue': p_value,
                f'{shock}_ci_lower': ci_lower,
                f'{shock}_ci_upper': ci_upper,
                f'{shock}_significant': p_value < 0.05
            })
    
    return results

def run_country_analysis(df, country_code):
    """
    Run complete LP analysis for a country
    """
    spec = COUNTRY_SPECS[country_code]
    print(f"\n{'='*70}")
    print(f"Running Enhanced LP Analysis: {spec['name']} ({country_code})")
    print(f"{'='*70}")
    print(f"Model specification: {spec['description']}")
    print(f"Shock variables: {spec['shock_vars']}")
    print(f"Control variables: {spec['control_vars']}")
    
    results_all = []
    
    for var in VARIABLES:
        print(f"\n--- Analyzing {var} ---")
        var_results = []
        
        for h in range(HORIZONS + 1):
            result = run_enhanced_lp(df, country_code, var, h, spec)
            
            if result:
                result['variable'] = var
                result['country'] = country_code
                var_results.append(result)
                
                # Print progress
                if h % 3 == 0:
                    shocks_info = []
                    for shock in spec['shock_vars']:
                        if f'{shock}_coef' in result:
                            coef = result[f'{shock}_coef']
                            se = result[f'{shock}_se']
                            pval = result[f'{shock}_pvalue']
                            sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
                            shocks_info.append(f"{shock}: {coef:.3f} ({se:.3f}){sig}")
                    
                    # Add interaction info to print
                    if 'Interaction_Gas_FX_coef' in result:
                         coef = result['Interaction_Gas_FX_coef']
                         pval = result['Interaction_Gas_FX_pvalue']
                         sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
                         shocks_info.append(f"Inter: {coef:.3f}{sig}")

                    
                    if shocks_info:
                        print(f"  h={h:2d}: {' | '.join(shocks_info)}")
        
        results_all.extend(var_results)
        
        # Plot IRF for this variable
        if var_results:
            plot_irf_with_ci(var_results, var, country_code, spec)
            
            # Plot interaction if available
            if spec.get('interaction', False):
                 plot_irf_interaction(var_results, var, country_code)

    
    # Convert to DataFrame
    if results_all:
        results_df = pd.DataFrame(results_all)
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, f"lp_enhanced_{country_code}.csv")
        results_df.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")
        
        # Print summary statistics
        print_summary_statistics(results_df, spec)
        
        return results_df
    else:
        print("No results generated")
        return None

def plot_irf_with_ci(results, variable, country, spec):
    """
    Plot IRF with confidence bands and significance indicators
    """
    results_df = pd.DataFrame(results)
    
    fig, axes = plt.subplots(1, len(spec['shock_vars']), figsize=(6*len(spec['shock_vars']), 5))
    if len(spec['shock_vars']) == 1:
        axes = [axes]
    
    for i, shock in enumerate(spec['shock_vars']):
        ax = axes[i]
        
        # Extract data
        horizons = results_df['horizon']
        coefs = results_df[f'{shock}_coef']
        ci_lower = results_df[f'{shock}_ci_lower']
        ci_upper = results_df[f'{shock}_ci_upper']
        significant = results_df[f'{shock}_significant']
        
        # Plot IRF
        ax.plot(horizons, coefs, 'o-', color='#1f77b4', linewidth=2, markersize=4, label='IRF')
        
        # Confidence band
        ax.fill_between(horizons, ci_lower, ci_upper, color='#1f77b4', alpha=0.2, label='95% CI')
        
        # Mark significant points
        sig_horizons = horizons[significant]
        sig_coefs = coefs[significant]
        if len(sig_horizons) > 0:
            ax.plot(sig_horizons, sig_coefs, 'ro', markersize=8, label='Significant (p<0.05)')
        
        # Formatting
        ax.axhline(0, color='black', linestyle='-', linewidth=0.8)
        ax.axvline(0, color='gray', linestyle=':', linewidth=1)
        ax.set_xlabel('Months')
        ax.set_ylabel('Response (% change in price level)')
        ax.set_title(f'{spec["name"]}: {variable}\nResponse to {shock}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add text box with key statistics
        max_h = np.argmax(np.abs(coefs))
        textstr = f'Max effect: {coefs.iloc[max_h]:.3f}\nat h={horizons.iloc[max_h]}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    # Save
    output_file = os.path.join(FIGURES_DIR, f"irf_enhanced_{country}_{variable}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  IRF plot saved: {output_file}")

def plot_irf_interaction(results, variable, country):
    """
    Plot IRF for interaction term specifically
    """
    results_df = pd.DataFrame(results)
    interaction = 'Interaction_Gas_FX'
    
    if f'{interaction}_coef' not in results_df.columns:
        return

    plt.figure(figsize=(8, 5))
    
    horizons = results_df['horizon']
    coefs = results_df[f'{interaction}_coef']
    ci_lower = results_df[f'{interaction}_ci_lower']
    ci_upper = results_df[f'{interaction}_ci_upper']
    
    plt.plot(horizons, coefs, 'o-', color='#9467bd', linewidth=2, label='Interaction Effect')
    plt.fill_between(horizons, ci_lower, ci_upper, color='#9467bd', alpha=0.2, label='95% CI')
    
    plt.axhline(0, color='black', linestyle='-', linewidth=0.8)
    plt.title(f'{country}: {variable}\nResponse to Gas Price × FX Depreciation Interaction')
    plt.xlabel('Months')
    plt.ylabel('Marginal Effect Amplifier')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_file = os.path.join(FIGURES_DIR, f"irf_interaction_{country}_{variable}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Interaction IRF plot saved: {output_file}")


def print_summary_statistics(results_df, spec):
    """
    Print summary statistics of LP results
    """
    print(f"\n{'='*70}")
    print("SUMMARY STATISTICS")
    print(f"{'='*70}")
    
    for var in VARIABLES:
        var_results = results_df[results_df['variable'] == var]
        if var_results.empty:
            continue
        
        print(f"\n{var}:")
        
        for shock in spec['shock_vars']:
            if f'{shock}_coef' not in var_results.columns:
                continue
            
            coefs = var_results[f'{shock}_coef']
            significant = var_results[f'{shock}_significant']
            
            max_effect = coefs.max()
            min_effect = coefs.min()
            max_abs_effect = coefs.abs().max()
            n_significant = significant.sum()
            
            print(f"  {shock}:")
            print(f"    Max positive effect: {max_effect:.3f}")
            print(f"    Max negative effect: {min_effect:.3f}")
            print(f"    Max absolute effect: {max_abs_effect:.3f}")
            print(f"    Significant horizons: {n_significant}/{len(var_results)}")

def main():
    if not os.path.exists(DATA_PATH):
        print("Data file not found")
        return
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Run analysis for both countries
    for country in ['ES', 'PL']:
        results = run_country_analysis(df, country)
        
        if results is not None:
            print(f"\nSuccessfully completed analysis for {country}")
        else:
            print(f"\nFailed to generate results for {country}")
    
    print(f"\n{'='*70}")
    print("All analyses completed!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
