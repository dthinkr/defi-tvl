import requests
import json
import os
import yaml
from tqdm import tqdm
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

def download_tvl_data(base_url, max_slugs=None):
    all_protocol_slugs = get_all_protocol_slugs()
    if max_slugs is not None:
        all_protocol_slugs = all_protocol_slugs[:max_slugs]
    
    failed_slugs = []

    for protocol in tqdm(all_protocol_slugs, desc="Downloading TVL data", unit="protocol"):
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

if __name__ == "__main__":
    run_data_ingestion(BASE_URL, MAX_SLUGS).serve()