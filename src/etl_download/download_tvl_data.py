import json
import os
import pickle
import requests
from tqdm import tqdm

# Configuration
DATA_DIR = "path/to/data"  # Update this path to your data directory
PROTOCOL_HEADERS_FILE = os.path.join(DATA_DIR, "protocol_headers.json")
FAILED_SLUGS_FILE = os.path.join(DATA_DIR, "failed_protocols.pkl")
BASE_URL = "https://api.llama.fi/"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

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

def download_protocol_headers():
    url = f"{BASE_URL}protocols"
    data = fetch_data(url)
    if data:
        save_data_to_file(data, PROTOCOL_HEADERS_FILE)
        print(f"Protocol headers saved to {PROTOCOL_HEADERS_FILE}")
    else:
        print("Failed to fetch protocol headers.")

def get_all_protocol_slugs():
    with open(PROTOCOL_HEADERS_FILE, "r") as f:
        headers = json.load(f)
    return [protocol["slug"] for protocol in headers]

def download_tvl_data():
    all_protocol_slugs = get_all_protocol_slugs()
    failed_slugs = []

    for protocol in tqdm(all_protocol_slugs, desc="Downloading TVL data", unit="protocol"):
        url = f"{BASE_URL}protocol/{protocol}"
        data = fetch_data(url)
        if data:
            filename = os.path.join(DATA_DIR, f"tvl/{protocol}.json")
            save_data_to_file(data, filename)
        else:
            failed_slugs.append(protocol)

    if failed_slugs:
        with open(FAILED_SLUGS_FILE, "wb") as f:
            pickle.dump(failed_slugs, f)
        print(f"\nFailed to fetch data for {len(failed_slugs)} protocols. Check '{FAILED_SLUGS_FILE}' for the list.")
    else:
        print("Successfully downloaded TVL data for all protocols.")

if __name__ == "__main__":
    download_protocol_headers()
    download_tvl_data()