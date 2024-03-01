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
import asyncio

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

def save_data_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

@task
async def download_protocol_headers():
    url = f"{BASE_URL}protocols"
    data = fetch_data(url)
    if data:
        save_data_to_file(data, PROTOCOL_HEADERS_FILE)
        df = pd.DataFrame(data)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)
        df.to_parquet(PROTOCOL_HEADERS_PARQUET, index=False)
        await upload_df_to_motherduck.fn(PROTOCOL_HEADERS_PARQUET, TABLES['A'])
    return data

def get_all_protocol_slugs():
    with open(PROTOCOL_HEADERS_FILE, "r") as f:
        headers = json.load(f)
    return [protocol["slug"] for protocol in headers]

@task(retries=3, retry_delay_seconds=[1, 10, 100])
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
        results.append([data.get('id', None), None, None, None, None, None])
    return pd.DataFrame(results, columns=['id', 'chain_name', 'date', 'token_name', 'quantity', 'value_usd'])

@task
async def process_single_file(file_path):
    df = extract_token_tvl(file_path)
    # Generate a unique file name for each protocol
    unique_file_name = os.path.basename(file_path).replace('.json', '_processed.parquet')
    parquet_file_path = os.path.join(DATA_DIR, unique_file_name)
    df.to_parquet(parquet_file_path, index=False)

async def clear_motherduck_table(tables: list):
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    for table in tables:
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER)")
        con.execute(f"TRUNCATE TABLE {table}")

@task
async def upload_df_to_motherduck(file_path, table_name):
    df = pd.read_parquet(file_path)
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    con.execute(f"INSERT INTO {table_name} SELECT * FROM '{file_path}'")

# Step 3: Modify download_and_process_single_protocol to call upload_df_to_motherduck after processing
@task
async def download_and_process_single_protocol(slug):
    url = f"{BASE_URL}protocol/{slug}"
    data = fetch_data(url)
    if data:
        filename = os.path.join(DATA_DIR, f"{slug}.json")
        save_data_to_file(data, filename)
        await process_single_file.fn(filename)
        # Upload the processed file to Motherduck
        processed_filename = filename.replace('.json', '_processed.parquet')
        await upload_df_to_motherduck.fn(processed_filename, TABLES['C'])
    else:
        with open(FAILED_SLUGS_FILE, "ab") as f:
            pickle.dump(slug, f)


@flow
async def run_data_ingestion():
    # Clear TABLE['C'] at the beginning
    await clear_motherduck_table([TABLES['A'],TABLES['C']])
    await download_protocol_headers()
    all_protocol_slugs = get_all_protocol_slugs()
    if MAX_SLUGS is not None:
        all_protocol_slugs = all_protocol_slugs[:MAX_SLUGS]

    tasks = [download_and_process_single_protocol(slug) for slug in all_protocol_slugs]
    await asyncio.gather(*tasks)

# Ensure clear_motherduck_table is not async; it's a synchronous operation.
# Adjust the rest of the code to fit this new approach.

if __name__ == "__main__":
    asyncio.run(run_data_ingestion())
