import requests
import json
import os
import yaml
import pickle
import pandas as pd
import glob
from prefect import task, flow
from config.config import TABLES, MD_TOKEN
import duckdb

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()
DATA_DIR = config['data_dir']
BASE_DIR = config['base_dir']
BASE_URL = config['base_url']
MAX_SLUGS = config.get('max_slugs', None)

os.makedirs(DATA_DIR, exist_ok=True)
PROTOCOL_HEADERS_FILE = os.path.join(BASE_DIR, "protocol_headers.json")
PROTOCOL_HEADERS_PARQUET = os.path.join(BASE_DIR, "protocol_headers.parquet")
FAILED_SLUGS_FILE = os.path.join(DATA_DIR, "failed_protocols.pkl")

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def save_data_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

@task
def download_protocol_headers():
    url = f"{BASE_URL}protocols"
    data = fetch_data(url)
    if data:
        save_data_to_file(data, PROTOCOL_HEADERS_FILE)
        df = pd.DataFrame(data)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)
        df.to_parquet(PROTOCOL_HEADERS_PARQUET, index=False)
    return data

def get_all_protocol_slugs():
    with open(PROTOCOL_HEADERS_FILE, "r") as f:
        headers = json.load(f)
    return [protocol["slug"] for protocol in headers]

@task
def download_tvl_data():
    all_protocol_slugs = get_all_protocol_slugs()
    if MAX_SLUGS is not None:
        all_protocol_slugs = all_protocol_slugs[:MAX_SLUGS]
    
    failed_slugs = []

    for protocol in all_protocol_slugs:
        url = f"{BASE_URL}protocol/{protocol}"
        data = fetch_data(url)
        if data:
            filename = os.path.join(DATA_DIR, f"{protocol}.json")
            save_data_to_file(data, filename)
        else:
            failed_slugs.append(protocol)

    if failed_slugs:
        with open(FAILED_SLUGS_FILE, "wb") as f:
            pickle.dump(failed_slugs, f)
        print(f"\nFailed to fetch data for {len(failed_slugs)} protocols. Check '{FAILED_SLUGS_FILE}' for the list.")
    else:
        print("Successfully downloaded TVL data for all protocols.")

def extract_token_tvl(file_path):
    results = []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        chains = data['chainTvls']
        tokens_list = data['tokens']
        tokens_in_usd_list = data['tokensInUsd']
        tokens_in_usd_dict = {item['date']: item['tokens'] for item in tokens_in_usd_list}
        for entry in tokens_list:
            date = entry['date']
            for chain_name, chain_data in chains.items():
                for token_name, quantity in entry['tokens'].items():
                    value_usd = tokens_in_usd_dict.get(date, {}).get(token_name, 0)
                    results.append([data['id'], chain_name, date, token_name, quantity, value_usd])
    except Exception as e:
        print(f"Error in extract_token_tvl: {e}")
        results.append([data.get('id', None), None, None, None, None, None])
    return pd.DataFrame(results, columns=['id', 'chain_name', 'date', 'token_name', 'quantity', 'value_usd'])

@task
def process_downloaded_data():
    folder_path = os.path.join(DATA_DIR, '*.json')
    json_files = glob.glob(folder_path)
    dfs = [extract_token_tvl(file) for file in json_files]
    unified_df = pd.concat(dfs, ignore_index=True)
    unified_df.to_parquet(os.path.join(DATA_DIR, f"{TABLES['C']}.parquet"), index=False)


@task
def upload_df_to_motherduck():
    path = os.path.join(DATA_DIR, f"{TABLES['C']}.parquet")
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    con.execute(f"CREATE TABLE IF NOT EXISTS {TABLES['C']} AS SELECT * FROM '{path}'")

@flow
def run_data_ingestion():
    download_protocol_headers()
    download_tvl_data()
    process_downloaded_data() 
    upload_df_to_motherduck()

if __name__ == "__main__":
    run_data_ingestion()