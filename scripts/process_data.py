import pandas as pd
import os
import io
import gzip
import numpy as np

# Config
RAW_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/raw"
PROCESSED_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Countries: Main Interest + Donors for SCM
# ES, PL (Main)
# Donor Pool for Spain: DE (Germany), FR (France), IT (Italy), AT (Austria), PT (Portugal - maybe check), NL (Netherlands)
COUNTRIES = ['PL', 'ES', 'DE', 'FR', 'IT', 'AT', 'PT', 'NL']

def read_eurostat_tsv(filename):
    """
    Reads a Eurostat TSV file (possibly gzipped) and returns a clean DataFrame.
    """
    filepath = os.path.join(RAW_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return pd.DataFrame()
        
    print(f"Processing {filepath}...")
    
    try:
        if filename.endswith('.gz'):
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                content = f.read()
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        
        df = pd.read_csv(io.StringIO(content), sep='\t')
        
        first_col = df.columns[0]
        id_vars = first_col.split('\\')[0].split(',')
        
        df[first_col] = df[first_col].str.strip()
        split_cols = df[first_col].str.split(',', expand=True)
        
        for i, var in enumerate(id_vars):
            df[var] = split_cols[i]
            
        df = df.drop(columns=[first_col])
        date_cols = [c for c in df.columns if c not in id_vars]
        
        melted = df.melt(id_vars=id_vars, value_vars=date_cols, var_name='time', value_name='value')
        
        melted['value'] = melted['value'].astype(str).str.strip()
        melted['value'] = melted['value'].replace(':', np.nan)
        melted['value'] = melted['value'].str.extract(r'([-+]?\d*\.?\d+)')[0]
        melted['value'] = pd.to_numeric(melted['value'], errors='coerce')
        melted['time'] = melted['time'].str.strip()
        
        return melted
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return pd.DataFrame()

def process_hicp():
    df = read_eurostat_tsv("prc_hicp_midx.tsv.gz")
    if df.empty: return None

    # DEBUG: Print unique values
    print("HICP Unique Geos:", df['geo'].unique())
    print("HICP Unique Units:", df['unit'].unique())
    print("HICP Unique Coicops (head):", df['coicop'].unique()[:10])

    df = df[df['geo'].isin(COUNTRIES)]
    print(f"HICP Rows after Country Filter: {len(df)}")
    print("Available Units for PL/ES:", df['unit'].unique())

    # Filter for Index
    # Prefer I15
    if df['unit'].str.contains('I15').any():
        print("Selecting I15 unit")
        df = df[df['unit'].str.contains('I15')]
    else:
        # Fallback to most common unit
        common_unit = df['unit'].mode()[0]
        print(f"I15 not found, selecting {common_unit}")
        df = df[df['unit'] == common_unit]
    
    print(f"HICP Rows after Unit Filter: {len(df)}")
    print("Available Coicops:", df['coicop'].unique())
    
    # Filter COICOP
    # Try broader codes if specific ones missing
    # CP00 is standard.
    # Core: CP00_X... might check full list
    # Let's map whatever starts with CP00... or just keep common ones.
    
    target_coicops = {
        'CP00': 'HICP_Total',
        'TOT_X_NRG_FOOD': 'HICP_Core', # Alternative code
        'CP00_X_NRG_FOOD': 'HICP_Core',
        'NRG': 'HICP_Energy'
    }
    
    # Flexible date parsing
    # Eurostat TSV might be YYYY-MM or YYYYMmm
    df['time_str'] = df['time'].str.replace('M', '-', regex=False)
    print(f"Time sample: {df['time'].head().tolist()}")
    df['date'] = pd.to_datetime(df['time_str'], errors='coerce')
    print(f"Date nulls: {df['date'].isna().sum()} / {len(df)}")
    if df['date'].isna().all():
         print("Date parsing failed with REPLACE 'M'. Trying default.")
         df['date'] = pd.to_datetime(df['time'], errors='coerce')
         print(f"Date nulls after retry: {df['date'].isna().sum()}")

    pivot = df.pivot_table(index=['geo', 'date'], columns='coicop', values='value').reset_index()
    pivot = pivot.rename(columns=target_coicops)
    return pivot

def process_ppi():
    df = read_eurostat_tsv("sts_inpp_m.tsv.gz")
    if df.empty: return None
    df = df[df['geo'].isin(COUNTRIES)]
    
    # Filter NACE
    # Try B-E or B-D or MIG_ING
    # B-E is standard.
    if 'nace_r2' in df.columns:
        print("PPI Nace:", df['nace_r2'].unique())
        # Use B-E (Industry total) if available, else B-D
        if df['nace_r2'].str.contains('B-E').any():
            df = df[df['nace_r2'] == 'B-E']
        elif df['nace_r2'].str.contains('B-D').any():
            df = df[df['nace_r2'].isin(['B-D'])]
        
    # Flexible date parsing
    df['time_str'] = df['time'].str.replace('M', '-', regex=False)
    df['date'] = pd.to_datetime(df['time_str'], errors='coerce')
    if df['date'].isna().all():
         df['date'] = pd.to_datetime(df['time'], errors='coerce')

    pivot = df.pivot_table(index=['geo', 'date'], values='value').reset_index()
    pivot = pivot.rename(columns={'value': 'PPI_Total'})
    return pivot

def process_ip():
    df = read_eurostat_tsv("sts_inpr_m.tsv.gz")
    if df.empty: return None
    df = df[df['geo'].isin(COUNTRIES)]
    
    # Filter S_ADJ
    if 's_adj' in df.columns:
        print("IP s_adj:", df['s_adj'].unique())
        if df['s_adj'].str.contains('SCA').any():
             df = df[df['s_adj'] == 'SCA']
        elif df['s_adj'].str.contains('SWDA').any():
             df = df[df['s_adj'] == 'SWDA']
    
    # Filter NACE
    if 'nace_r2' in df.columns:
         if df['nace_r2'].str.contains('B-D').any():
             df = df[df['nace_r2'] == 'B-D']
         elif df['nace_r2'].str.contains('C').any(): # Manufacturing
             df = df[df['nace_r2'] == 'C']
         
    # Flexible date parsing
    df['time_str'] = df['time'].str.replace('M', '-', regex=False)
    df['date'] = pd.to_datetime(df['time_str'], errors='coerce')
    if df['date'].isna().all():
         df['date'] = pd.to_datetime(df['time'], errors='coerce')

    pivot = df.pivot_table(index=['geo', 'date'], values='value').reset_index()
    pivot = pivot.rename(columns={'value': 'IP_Total'})
    return pivot

def process_oil():
    # Try Stooq
    path = os.path.join(RAW_DIR, "brent_oil_price_stooq.csv")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        try:
            df = pd.read_csv(path)
            # Stooq: Date, Open, High, Low, Close, Volume
            df['date'] = pd.to_datetime(df['Date'])
            df = df[['date', 'Close']].rename(columns={'Close': 'f_OIL'})
            df['date'] = df['date'] + pd.offsets.MonthBegin(0)
            return df
        except:
            pass

    # Try FRED
    path = os.path.join(RAW_DIR, "brent_oil_price_fred.csv")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        df = pd.read_csv(path)
        # FRED: DATE, DCOILBRENTEU
        df['date'] = pd.to_datetime(df['DATE'])
        df = df[['date', 'DCOILBRENTEU']].rename(columns={'DCOILBRENTEU': 'f_OIL'})
        df['date'] = df['date'] + pd.offsets.MonthBegin(0)
        return df

    # Fallback to Yahoo
    path = os.path.join(RAW_DIR, "brent_oil_price.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['Date'])
        df = df[['date', 'Adj Close']].rename(columns={'Adj Close': 'f_OIL'})
        df['date'] = df['date'] + pd.offsets.MonthBegin(0)
        return df
        
    return None

def process_ecb():
    path = os.path.join(RAW_DIR, "ecb_pln_eur.csv")
    if not os.path.exists(path): return None
    
    # ECB CSV format usually: KEY, FREQ, ..., TIME_PERIOD, OBS_VALUE
    df = pd.read_csv(path)
    # Check columns
    if 'TIME_PERIOD' in df.columns and 'OBS_VALUE' in df.columns:
        df['date'] = pd.to_datetime(df['TIME_PERIOD'])
        df = df[['date', 'OBS_VALUE']].rename(columns={'OBS_VALUE': 'f_PLN_EUR'})
        # Since this is PLN/EUR, it applies to Poland.
        # Spain currency is EUR (rate=1 or irrelevant for exchange rate shock relative to non-euro?)
        # We might want USD/EUR for Spain?
        # For now, keep PLN/EUR for Poland.
        return df
    return None

def process_gas():
    # FRED IMF Gas
    path = os.path.join(RAW_DIR, "gas_price_imf.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        # FRED: DATE, PNGASEUUSDM
        df['date'] = pd.to_datetime(df['DATE'])
        df = df[['date', 'PNGASEUUSDM']].rename(columns={'PNGASEUUSDM': 'f_GAS'})
        df['date'] = df['date'] + pd.offsets.MonthBegin(0)
        return df
    return None

def process_usd_eur():
    # FRED USD/EUR
    path = os.path.join(RAW_DIR, "usd_eur_rate.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        # FRED: DATE, DEXUSEU
        df['date'] = pd.to_datetime(df['DATE'])
        df = df[['date', 'DEXUSEU']].rename(columns={'DEXUSEU': 'f_USD_EUR'})
        df['date'] = df['date'] + pd.offsets.MonthBegin(0)
        return df
    return None

def process_ea_ip():
    # Eurostat sts_inpr_m (already fetched)
    # Extract EA20 
    df = read_eurostat_tsv("sts_inpr_m.tsv.gz")
    if df.empty: return None
    
    # Filter for EA20 (Euro Area) and S_ADJ=SCA/SWDA, NACE=B-D
    df = df[df['geo'].isin(['EA20', 'EA19'])] # Try both
    
    if 's_adj' in df.columns:
        if df['s_adj'].str.contains('SCA').any():
             df = df[df['s_adj'] == 'SCA']
        elif df['s_adj'].str.contains('SWDA').any():
             df = df[df['s_adj'] == 'SWDA']

    if 'nace_r2' in df.columns:
         if df['nace_r2'].str.contains('B-D').any():
             df = df[df['nace_r2'].isin(['B-D'])]
    
    # Flexible date parsing
    df['time_str'] = df['time'].str.replace('M', '-', regex=False)
    df['date'] = pd.to_datetime(df['time_str'], errors='coerce')
    if df['date'].isna().all():
         df['date'] = pd.to_datetime(df['time'], errors='coerce')
         
    pivot = df.pivot_table(index=['date'], values='value').reset_index()
    # Average if multiple Geos (EA19 vs EA20 overlaps)
    pivot = pivot.groupby('date')['value'].mean().reset_index()
    pivot = pivot.rename(columns={'value': 'EA_IP_Total'})
    return pivot

def main():
    print("Processing datasets...")
    
    # 1. Main Country Panel
    hicp = process_hicp()
    # ppi = process_ppi() # Excluded
    ip = process_ip()
    
    merged = hicp
    if ip is not None:
        merged = pd.merge(merged, ip, on=['geo', 'date'], how='outer')
        
    # 2. External Variables
    oil = process_oil()
    ecb = process_ecb() # PLN/EUR
    
    # New Vars
    gas = process_gas()
    usd_eur = process_usd_eur()
    ea_ip = process_ea_ip()
    
    # Merge Ext
    for ext in [oil, ecb, gas, usd_eur, ea_ip]:
        if ext is not None:
            merged = pd.merge(merged, ext, on='date', how='left')
            
    # 3. Construct Local Currency Shocks
    print("Constructing Local Currency Shocks...")
    
    # Construct Exchange Rates needed for all rows
    # XR_USD_EUR: USD per 1 EUR. (DEXUSEU)
    # XR_PLN_EUR: PLN per 1 EUR. (f_PLN_EUR)
    # Target: Oil Price in Local Currency.
    # Spain (EUR): Oil_USD / (USD/EUR) = Oil_USD * (EUR/USD) = Oil_USD * (1/DEXUSEU).
    # Poland (PLN): Oil_USD * (PLN/USD).
    # PLN/USD = (PLN/EUR) * (EUR/USD) = f_PLN_EUR * (1/DEXUSEU).
    
    # 3. Construct Specific Variables for Regression
    print("Constructing Regression Variables...")
    
    # Fill Gas if missing (forward fill for minor gaps?)
    if 'f_GAS' in merged.columns:
        merged['f_GAS'] = merged['f_GAS'].ffill()
    
    # 1. Global Gas Price (EUR) NOT USD
    # We convert USD Gas Price to EUR using USD/EUR Exchange Rate.
    # P_Gas_EUR = P_Gas_USD / (USD/EUR) 
    # (since DEXUSEU is USD per 1 EUR).
    
    if 'f_GAS' in merged.columns and 'f_USD_EUR' in merged.columns:
        merged['Gas_EUR'] = merged['f_GAS'] / merged['f_USD_EUR']
        merged['Log_Gas_EUR'] = np.log(merged['Gas_EUR'])
        merged['DL_Gas_EUR'] = merged['Log_Gas_EUR'].diff() * 100 # Percentage Change
        
        # Also keep USD Gas for reference
        merged['DL_Gas_USD'] = np.log(merged['f_GAS']).diff() * 100
    
    # 2. Exchange Rates (Local Currency per 1 EUR)
    # Target: Increase = Depreciation against the Euro (The Anchor)
    
    # Spain: EUR. Exchange rate against EUR is 1 (Log Change 0).
    # Poland: PLN/EUR (f_PLN_EUR).
    
    merged['DL_XR_Local'] = 0.0 # Default 0 (for Spain)

    # Poland: FX Shock = Delta Log PLN/EUR
    if 'f_PLN_EUR' in merged.columns:
        pln_log = np.log(merged['f_PLN_EUR'])
        pln_diff = pln_log.diff() * 100
        
        # Apply only to PL rows
        mask_pl = merged['geo'] == 'PL'
        # We need to ensure alignment. The diff is on the full series?
        # f_PLN_EUR is a column. We can just map it.
        # But we must be careful about dates.
        # It's better to calculate diff on the column and fill.
        
        merged['DL_XR_PLN_EUR'] = pln_diff
        merged.loc[mask_pl, 'DL_XR_Local'] = merged.loc[mask_pl, 'DL_XR_PLN_EUR']
     
    # For Spain, DL_XR_Local remains 0.


    # Save
    if merged is not None:
        merged = merged.sort_values(by=['geo', 'date'])
        out_path = os.path.join(PROCESSED_DIR, "merged_data.csv")
        merged.to_csv(out_path, index=False)
        print(f"Saved merged data to {out_path}")
        # Debug
        cols = ['geo', 'date', 'DL_Gas_USD', 'DL_XR_Local']
        print(merged[cols].tail())

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
