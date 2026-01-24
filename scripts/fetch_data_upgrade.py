import pandas as pd
import pandas_datareader.data as web
import os
import requests
from io import StringIO

# Config
RAW_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_fred_data():
    print("Fetching data from FRED...")
    try:
        # 1. Dutch TTF Gas (Proxy: IMF Global Price of Natural Gas, EU import price)
        # Symbol: PNGASEUUSDM (Global price of Natural Gas, EU, USD/MMBtu)
        # This is a very standard proxy when TTF spot is hard to get.
        gas = web.DataReader('PNGASEUUSDM', 'fred', start='2015-01-01')
        gas.to_csv(os.path.join(RAW_DIR, "gas_price_imf.csv"))
        print("Saved Gas Price (PNGASEUUSDM).")
        
        # 2. USD/EUR Exchange Rate
        # DERSEUR? No, DEXUSEU (US Dollars to One Euro) i.e. 1 EUR = X USD.
        # So Price_EUR = Price_USD / DEXUSEU
        xr = web.DataReader('DEXUSEU', 'fred', start='2015-01-01')
        # Resample to Monthly Average
        xr_monthly = xr.resample('ME').mean() 
        xr_monthly.to_csv(os.path.join(RAW_DIR, "usd_eur_rate.csv"))
        print("Saved USD/EUR Rate.")
        
    except Exception as e:
        print(f"FRED fetch failed: {e}")

def fetch_eurostat_ea_ip():
    print("Fetching Euro Area IP (Demand Proxy)...")
    # sts_inpr_m is already downloaded! 
    # We just need to make sure we process 'EA20' or 'EA19' from it in process_data.py
    # So no new download needed if the file is comprehensive.
    # But just in case, let's confirm we have it.
    path = os.path.join(RAW_DIR, "sts_inpr_m.tsv.gz")
    if os.path.exists(path):
        print("Eurostat IP file exists. Will extract EA aggregates in processing.")
    else:
        print("Eurostat IP file missing! This should not happen if previous steps succeeded.")

if __name__ == "__main__":
    fetch_fred_data()
    fetch_eurostat_ea_ip()
