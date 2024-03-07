import requests
import json
import os
import yaml
import pickle
import pandas as pd
from prefect import task, flow, get_run_logger
from config.config import TABLES, MD_TOKEN, CATEGORY_MAPPING
import duckdb
import asyncio
import psutil
from config.etl_network import ETLNetwork
from config.query import MotherduckClient
import hashlib


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
        df['type'] = 'default'
        df.to_parquet(PROTOCOL_HEADERS_PARQUET, index=False)
        await upload_df_to_motherduck.fn(PROTOCOL_HEADERS_PARQUET, TABLES['A'])
        await add_type_column.fn()
        os.remove(PROTOCOL_HEADERS_FILE)
        os.remove(PROTOCOL_HEADERS_PARQUET)
    else: 
        get_run_logger().info("No data found in the API response.")
    return data

@task
async def add_type_column():
    con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
    con.execute(f"ALTER TABLE {TABLES['A']} ADD COLUMN IF NOT EXISTS type VARCHAR;")

    category_to_type = {}
    for type_name, categories in CATEGORY_MAPPING.items():
        for category in categories:
            category_to_type[category] = type_name
    
    for category, type_name in category_to_type.items():
        update_query = f"""
        UPDATE {TABLES['A']}
        SET type = '{type_name}'
        WHERE category = '{category}';
        """
        con.execute(update_query)
    
    con.close()

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

def extract_token_tvl(file_path):
    results = []
    with open(file_path, 'r') as f:
        data = json.load(f)

    for chain_name, chain_data in data['chainTvls'].items():
        tokens_usd = chain_data['tokensInUsd']
        tokens_quantity = chain_data['tokens']

        for usd_entry, quantity_entry in zip(tokens_usd, tokens_quantity):
            date = usd_entry['date']
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
async def process_single_file(con, json_file_path, parquet_file_path):
    df = extract_token_tvl(json_file_path)
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
async def upload_df_to_motherduck(parquet_file_path, table_name, con=duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')):
    # Generate a unique hash for the file path to use as the temporary table name
    file_path_hash = hashlib.md5(parquet_file_path.encode()).hexdigest()
    temp_table_name = f"temp_{file_path_hash}"

    # Create a temporary table from the Parquet file
    con.execute(f"CREATE TEMPORARY TABLE {temp_table_name} AS SELECT * FROM read_parquet('{parquet_file_path}')")

    if table_name == TABLES['A']:  # Assuming TABLES['A'] holds the name of table A
        # For table A, only check if there is a new id
        con.execute(f"""
        INSERT INTO {table_name}
        SELECT t.*
        FROM {temp_table_name} t
        WHERE NOT EXISTS (
            SELECT 1 FROM {table_name} tt
            WHERE tt.id = t.id
        )
        """)
    elif table_name == TABLES['C']:
        # For other tables, use the existing logic
        con.execute(f"""
        INSERT INTO {table_name} (id, chain_name, token_name, date, quantity, value_usd)
        SELECT t.id, t.chain_name, t.token_name, t.date, t.quantity, t.value_usd
        FROM {temp_table_name} t
        WHERE NOT EXISTS (
            SELECT 1 FROM {table_name} tt
            WHERE tt.id = t.id 
            AND tt.chain_name = t.chain_name 
            AND tt.token_name = t.token_name 
            AND tt.date = t.date
        )
        """)

    # Optionally, drop the temporary table
    con.execute(f"DROP TABLE IF EXISTS {temp_table_name}")

    con.close()

@task
async def download_and_process_single_protocol(slug):
    url = f"{BASE_URL}protocol/{slug}"
    data = fetch_data(url)
    if data:
        con = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
        json_file_path = os.path.join(DATA_DIR, f"{slug}.json")
        parquet_file_path = os.path.join(DATA_DIR, f"{slug}.parquet")
        save_data_to_file(data, json_file_path)
        await process_single_file.fn(con, json_file_path, parquet_file_path)
        os.remove(json_file_path)

@task
async def update_mapping():
    bq = MotherduckClient()
    etl = ETLNetwork(bq=bq)
    etl.update_mapping()

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

    await update_mapping()

if __name__ == "__main__":
    asyncio.run(llama_ingest())