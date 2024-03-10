import pandas as pd
import sys
import requests
from datetime import datetime
import numpy as np

def fetch_historical_all_chains_tvl_to_df():
    url = "https://api.llama.fi/v2/historicalChainTvl"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], unit='s').dt.strftime('%Y-%m-%d')
        df['tvl'] = df['tvl'].replace('0NaN', np.nan)
        df['tvl'] = df['tvl'] / 1e9
        df.dropna(inplace=True)  # Drop rows with NaN values
        return df
    else:
        return None

df = fetch_historical_all_chains_tvl_to_df()
if df is not None:
    sys.stdout.write(df.to_csv(index=False))
else:
    sys.stdout.write("Failed to fetch data.")