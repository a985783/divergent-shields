
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import os
import requests
import pandas as pd
import io
from datetime import datetime

# Setup directories
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_eurostat_data(code, name):
    """
    Fetches data from Eurostat (TSV format) and saves it to data/raw.
    Using the bulk download facility which is often more reliable for full datasets.
    """
    print(f"Fetching {name} ({code})...")
    # Eurostat Bulk Download URL (TSV format)
    # The modern API endpoint that returns GZIP TSV
    url = f"https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{code}?format=TSV&compressed=true"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save compressed file
        file_path = os.path.join(RAW_DIR, f"{code}.tsv.gz")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved {file_path}")
        return True
    except Exception as e:
        print(f"Failed to fetch {code}: {e}")
        return False

def fetch_yahoo_data(ticker, name, start="2015-01-01"):
    """
    Fetches data from Yahoo Finance via direct CSV download.
    """
    print(f"Fetching {name} ({ticker})...")
    # Yahoo Finance download URL
    period1 = int(pd.Timestamp(start).timestamp())
    period2 = int(datetime.now().timestamp())
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval=1mo&events=history&includeAdjustedClose=true"
    
    try:
        # User-Agent is required for Yahoo
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        file_path = os.path.join(RAW_DIR, f"{name.lower().replace(' ', '_')}.csv")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved {file_path}")
        return True
    except Exception as e:
        print(f"Failed to fetch {name}: {e}")
        return False

def fetch_ecb_data():
    """
    Fetches PLN/EUR exchange rate from ECB Data Portal (SDMX/CSV).
    """
    print("Fetching PLN/EUR Exchange Rate...")
    # EXR.M.PLN.EUR.SP00.A (Monthly, PLN to EUR, Spot, Average)
    url = "https://data-api.ecb.europa.eu/service/data/EXR/M.PLN.EUR.SP00.A?format=csvdata"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        file_path = os.path.join(RAW_DIR, "ecb_pln_eur.csv")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved {file_path}")
        return True
    except Exception as e:
        print(f"Failed to fetch ECB data: {e}")
        return False

def main():
    print("Starting data collection...")
    
    # 1. Inflation (HICP) - Monthly Index
    # prc_hicp_midx: HICP - monthly data (index)
    fetch_eurostat_data("prc_hicp_midx", "HICP (All-items & Sub-indices)")
    
    # 2. PPI - Domestic output prices
    # sts_inpp_m: Industrial producer prices - monthly data
    fetch_eurostat_data("sts_inpp_m", "PPI (Industrial Producer Prices)")
    
    # 3. Industrial Production
    # sts_inpr_m: Industrial production - monthly data
    fetch_eurostat_data("sts_inpr_m", "Industrial Production")
    
    # 4. Exports (Volume/Value)
    # ei_eteu27_2020_m for EU27 trade indicators
    fetch_eurostat_data("ei_eteu27_2020_m", "International Trade Indicators")
    
    # 5. Brent Oil Price
    # Symbol: BZ=F
    fetch_yahoo_data("BZ=F", "Brent Oil Price")
    
    # 6. Exchange Rate (PLN/EUR)
    fetch_ecb_data()
    
    print("Data collection complete.")

if __name__ == "__main__":
    main()
