import requests
import json
import os
import yaml
import pickle
from prefect import task, flow

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()
DATA_DIR = config['data_dir']
BASE_URL = config['base_url']
MAX_SLUGS = config.get('max_slugs', None)

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
PROTOCOL_HEADERS_FILE = os.path.join(DATA_DIR, "protocol_headers.json")
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
def download_protocol_headers(base_url):
    url = f"{base_url}protocols"
    data = fetch_data(url)
    if data:
        save_data_to_file(data, PROTOCOL_HEADERS_FILE)
        print(f"Protocol headers saved to {PROTOCOL_HEADERS_FILE}")
    else:
        print("Failed to fetch protocol headers.")
    return data

def get_all_protocol_slugs():
    with open(PROTOCOL_HEADERS_FILE, "r") as f:
        headers = json.load(f)
    return [protocol["slug"] for protocol in headers]

@task
def download_tvl_data(base_url, max_slugs=None):
    all_protocol_slugs = get_all_protocol_slugs()
    if max_slugs is not None:
        all_protocol_slugs = all_protocol_slugs[:max_slugs]
    
    failed_slugs = []

    for protocol in all_protocol_slugs:
        url = f"{base_url}protocol/{protocol}"
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

@flow
def run_data_ingestion(base_url, max_slugs=None):
    download_protocol_headers(base_url)
    download_tvl_data(base_url, max_slugs)


import pandas as pd
import glob

@task
def load_and_process_json_files(data_dir):
    """
    Load JSON files from the specified directory, process them, and return a single DataFrame.
    """
    json_pattern = os.path.join(data_dir, '*.json')
    file_list = glob.glob(json_pattern)

    df_list = []
    for file in file_list:
        with open(file, 'r') as f:
            data = json.load(f)
            df = pd.json_normalize(data)
            df_list.append(df)

    # Combine all DataFrames into a single DataFrame
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

@task
def save_to_parquet(df, output_dir, filename='combined_data.parquet'):
    """
    Save the DataFrame to a Parquet file in the specified output directory.
    """
    output_path = os.path.join(output_dir, filename)
    df.to_parquet(output_path, engine='pyarrow')

@flow
def process_data_to_parquet(data_dir):
    """
    Main function to load, process, and save the combined data to a Parquet file.
    """
    combined_df = load_and_process_json_files(data_dir)
    save_to_parquet(combined_df, data_dir)  # Saving to the same directory as JSON files

if __name__ == "__main__":
    # run_data_ingestion(BASE_URL, MAX_SLUGS)
    process_data_to_parquet(DATA_DIR)  # Call this function after downloading the JSON files
