import requests
import json
import os
import yaml
import pickle
import pandas as pd
from prefect import task, flow, get_run_logger
from config.config import TABLES, MD_TOKEN
import duckdb
import asyncio
import psutil
from datetime import datetime

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
        os.remove(PROTOCOL_HEADERS_FILE)
        os.remove(PROTOCOL_HEADERS_PARQUET)
    else: 
        get_run_logger().info("No data found in the API response.")
    return data

def get_all_protocol_slugs():
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    query = f"SELECT DISTINCT slug FROM {TABLES['A']}"
    result = con.execute(query).fetchall()
    con.close()
    return [row[0] for row in result]

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

def extract_token_tvl(file_path, latest_date=None):
    results = []
    with open(file_path, 'r') as f:
        data = json.load(f)

    for chain_name, chain_data in data['chainTvls'].items():
        tokens_usd = chain_data['tokensInUsd']
        tokens_quantity = chain_data['tokens']

        for usd_entry, quantity_entry in zip(tokens_usd, tokens_quantity):
            date = usd_entry['date']
            if latest_date is not None and date <= latest_date:
                continue
            for token_name, value_usd in usd_entry['tokens'].items():
                quantity = quantity_entry['tokens'].get(token_name, 0)
                results.append([data['id'], chain_name, date, token_name, quantity, value_usd])

    df = pd.DataFrame(results, columns=['id', 'chain_name', 'date', 'token_name', 'quantity', 'value_usd'])
    df['quantity'] = df['quantity'].astype('float64')
    df['value_usd'] = df['value_usd'].astype('float64')
    
    if df.empty:
        get_run_logger().info(f"No new data found in {file_path}.")
    return df

@task
async def process_single_file(con, json_file_path, parquet_file_path, latest_date=None):
    df = extract_token_tvl(json_file_path, latest_date)
    if not df.empty:
        df.to_parquet(parquet_file_path, index=False)
        await upload_df_to_motherduck.fn(parquet_file_path, TABLES['C'], con)
        os.remove(parquet_file_path)

async def clear_motherduck_table(tables: list):
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    for table in tables:
        exists = con.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')").fetchone()[0]
        if exists:
            con.execute(f"DELETE FROM {table}")
        
@task(retries=3, retry_delay_seconds=[1, 10, 100])
async def upload_df_to_motherduck(file_path, table_name, con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')):
    """TODO: WRITE WRITE CONFCLIT WHEN TABLE C DOES NOT EXIST. 
    duckdb.duckdb.TransactionException: TransactionContext Error: Catalog write-write conflict on create with "C_protocol_token_tvl"""
    # con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    # con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM '{file_path}'")
    con.execute(f"INSERT INTO {table_name} SELECT * FROM '{file_path}'")
    con.close()

@task
async def download_and_process_single_protocol(slug):
    url = f"{BASE_URL}protocol/{slug}"
    data = fetch_data(url)
    if data:
        con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
        unique_id = data['id']
        latest_date_query = f"SELECT MAX(date) FROM {TABLES['C']} WHERE id = '{unique_id}'"
        latest_date_result = con.execute(latest_date_query).fetchone()
        latest_date = latest_date_result[0] if latest_date_result else None
        json_file_path = os.path.join(DATA_DIR, f"{slug}.json")
        parquet_file_path = os.path.join(DATA_DIR, f"{slug}.parquet")
        save_data_to_file(data, json_file_path)
        
        await process_single_file.fn(con, json_file_path, parquet_file_path, latest_date)
        os.remove(json_file_path)

def _get_system_memory_info_gb():
    mem = psutil.virtual_memory()
    return mem.total / (1024.0 ** 3)

def _calculate_concurrent_tasks(memory_per_task_gb=20/200, safety_factor=config['safety_factor']):
    total_memory_gb = _get_system_memory_info_gb()
    usable_memory_gb = total_memory_gb * safety_factor
    max_concurrent_tasks_based_on_memory = int(usable_memory_gb / memory_per_task_gb)
    return max_concurrent_tasks_based_on_memory

@flow
async def llama_ingest():

    await clear_motherduck_table([TABLES['A']])
    await download_protocol_headers()
    all_protocol_slugs = get_all_protocol_slugs()[:MAX_SLUGS]

    max_concurrent_tasks = _calculate_concurrent_tasks()
    total_slugs_to_process = len(all_protocol_slugs) if MAX_SLUGS is None else min(len(all_protocol_slugs), MAX_SLUGS)

    for i in range(0, total_slugs_to_process, max_concurrent_tasks):
        batch_slugs = all_protocol_slugs[i:i+max_concurrent_tasks]
        tasks = [download_and_process_single_protocol(slug) for slug in batch_slugs]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(llama_ingest())