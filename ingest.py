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
import psutil

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
    df = pd.DataFrame(results, columns=['id', 'chain_name', 'date', 'token_name', 'quantity', 'value_usd'])
    df['quantity'] = df['quantity'].astype('float64')
    df['value_usd'] = df['value_usd'].astype('float64')
    return df

@task
async def process_single_file(file_path):
    df = extract_token_tvl(file_path)
    # Generate a unique file name for each protocol
    unique_file_name = os.path.basename(file_path).replace('.json', '.parquet')
    parquet_file_path = os.path.join(DATA_DIR, unique_file_name)
    df.to_parquet(parquet_file_path, index=False)

async def clear_motherduck_table(tables: list):
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    for table in tables:
        exists = con.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')").fetchone()[0]
        if exists:
            con.execute(f"DELETE FROM {table}")
        
@task
async def upload_df_to_motherduck(file_path, table_name):
    """TODO: WRITE WRITE CONFCLIT WHEN TABLE C DOES NOT EXIST. 
    duckdb.duckdb.TransactionException: TransactionContext Error: Catalog write-write conflict on create with "C_protocol_token_tvl"""
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    # con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM '{file_path}'")
    con.execute(f"INSERT INTO {table_name} SELECT * FROM '{file_path}'")

@task
async def download_and_process_single_protocol(slug):
    url = f"{BASE_URL}protocol/{slug}"
    data = fetch_data(url)
    if data:
        filename = os.path.join(DATA_DIR, f"{slug}.json")
        save_data_to_file(data, filename)
        await process_single_file.fn(filename)
        processed_filename = filename.replace('.json', '.parquet')
        await upload_df_to_motherduck.fn(processed_filename, TABLES['C'])
        os.remove(filename)
        os.remove(processed_filename)
    else:
        with open(FAILED_SLUGS_FILE, "ab") as f:
            pickle.dump(slug, f)


def _get_system_memory_info_gb():
    mem = psutil.virtual_memory()
    return mem.total / (1024.0 ** 3)  # Convert bytes to GB

def _calculate_concurrent_tasks(memory_per_task_gb=20/200, safety_factor=1.2):
    total_memory_gb = _get_system_memory_info_gb()
    usable_memory_gb = total_memory_gb * safety_factor
    max_concurrent_tasks_based_on_memory = int(usable_memory_gb / memory_per_task_gb)
    return max_concurrent_tasks_based_on_memory

@flow
async def llama_ingest():
    await clear_motherduck_table([TABLES['A']])
    await download_protocol_headers()
    all_protocol_slugs = get_all_protocol_slugs()

    max_concurrent_tasks = _calculate_concurrent_tasks()
    total_slugs_to_process = len(all_protocol_slugs) if MAX_SLUGS is None else min(len(all_protocol_slugs), MAX_SLUGS)

    # Process all slugs in batches, respecting the memory constraints
    for i in range(0, total_slugs_to_process, max_concurrent_tasks):
        # Determine the slugs for the current batch
        batch_slugs = all_protocol_slugs[i:i+max_concurrent_tasks]
        # Create and await tasks for the current batch
        tasks = [download_and_process_single_protocol(slug) for slug in batch_slugs]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(llama_ingest())