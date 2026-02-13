
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Config
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
TABLES_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

def plot_time_series(df, variable, title, filename):
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='date', y=variable, hue='geo')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Index / Value')
    plt.grid(True)
    plt.savefig(os.path.join(FIGURES_DIR, filename))
    plt.close()

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found: {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate YoY Growth for Indices (if needed)
    # Eurostat Indices are usually 2015=100. Growth = (t / t-12) - 1
    # We should ensure data is sorted
    df = df.sort_values(by=['geo', 'date'])
    
    for col in ['HICP_Total', 'HICP_Core', 'HICP_Energy', 'IP_Total']:
        if col in df.columns:
            # Calculate YoY
            df[f'{col}_YoY'] = df.groupby('geo')[col].pct_change(12) * 100
            
            # Plot Levels
            plot_time_series(df, col, f'{col} Level', f'{col}_level.png')
            # Plot YoY
            plot_time_series(df, f'{col}_YoY', f'{col} YoY Growth (%)', f'{col}_yoy.png')

    # Oil Price Plot
    if 'f_OIL' in df.columns:
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df, x='date', y='f_OIL', label='Brent Oil (USD)', color='black')
        plt.title('Brent Oil Price')
        plt.grid(True)
        plt.savefig(os.path.join(FIGURES_DIR, 'oil_price.png'))
        plt.close()

    # Descriptive Stats
    desc = df.groupby('geo')[['HICP_Total_YoY', 'HICP_Core_YoY', 'IP_Total_YoY']].describe().T
    desc.to_csv(os.path.join(TABLES_DIR, 'descriptive_stats.csv'))
    print("Descriptive analysis complete. Figures and tables saved.")

if __name__ == "__main__":
    main()
