import requests
import os
import pandas as pd
from io import StringIO

# Config
RAW_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_oil_manual():
    print("Fetching Brent Oil Price...")
    # Using a reliable direct CSV source if Stooq fails.
    # U.S. Energy Information Administration (EIA) or FRED is best.
    # But authentic public URL without key?
    # Europe Brent Spot Price FOB (Dollars per Barrel)
    # https://stooq.com/q/d/l/?s=b.f&i=m often works.
    
    # Let's try to simulate a browser request to Stooq again with better headers.
    url = "https://stooq.com/q/d/l/?s=cb.f&i=m"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        content = response.text
        if "Date" not in content and "Close" not in content:
            print("Stooq returned invalid content (likely blocked).")
            # Fallback: Create a small dummy dataset for functionality if real fetch fails?
            # User wants "Authentic" data.
            # Use 'pandas_datareader' if available?
            # Let's try FRED via pandas_datareader if installed.
            try:
                import pandas_datareader.data as web
                # DCOILBRENTEU is Brent Crude Oil, daily.
                # We need monthly.
                print("Attempting pandas_datareader (FRED)...")
                df = web.DataReader('DCOILBRENTEU', 'fred', start='2015-01-01')
                # Resample to Monthly
                df = df.resample('M').mean()
                df.to_csv(os.path.join(RAW_DIR, "brent_oil_price_fred.csv"))
                print("Saved FRED data.")
                return True
            except Exception as e:
                print(f"FRED fetch failed: {e}")
                # Fallback to a hardcoded URL from a dataset repo?
                return False
        
        # Save Stooq
        path = os.path.join(RAW_DIR, "brent_oil_price_stooq.csv")
        with open(path, 'wb') as f:
            f.write(response.content)
        print(f"Saved {path}")
        return True
        
    except Exception as e:
        print(f"Fetch failed: {e}")
        return False

if __name__ == "__main__":
    fetch_oil_manual()
