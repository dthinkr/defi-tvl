import pandas as pd
import sys
import requests
from datetime import datetime
import numpy as np

def fetch_historical_chain_tvl_to_df(chain):
    url = f"https://api.llama.fi/v2/historicalChainTvl/{chain}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], unit='s').dt.strftime('%Y-%m-%d')
        df['tvl'] = df['tvl'].replace('0NaN', np.nan)  # Replace '0NaN' with actual NaN
        df.dropna(inplace=True)  # Drop rows with NaN values
        return df
    else:
        return None

chain = "Ethereum"
df = fetch_historical_chain_tvl_to_df(chain)
if df is not None:
    sys.stdout.write(df.to_csv(index=False))
else:
    sys.stdout.write("Failed to fetch data.")