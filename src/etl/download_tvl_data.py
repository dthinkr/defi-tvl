import json
import pickle

import requests
from tqdm import tqdm


def fetch_tvl_data(protocol_slug):
    base_url = "https://api.llama.fi/protocol/"
    response = requests.get(base_url + protocol_slug)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {protocol_slug}: {response.status_code}")
        return None


def save_data_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def get_all_protocol_slugs():
    with open("../data/headers/protocol_headers.json", "r") as f:
        headers = json.load(f)
    return [protocol["slug"] for protocol in headers]


def save_failed_slugs_to_pickle(failed_slugs):
    with open("failed_protocols.pkl", "wb") as f:
        pickle.dump(failed_slugs, f)


all_protocol_slugs = get_all_protocol_slugs()
failed_slugs = []

for protocol in tqdm(all_protocol_slugs, desc="Downloading data", unit="protocol"):
    data = fetch_tvl_data(protocol)
    if data:
        filename = f"../data/tvl/{protocol}.json"
        save_data_to_file(data, filename)
    else:
        failed_slugs.append(protocol)

save_failed_slugs_to_pickle(failed_slugs)
if failed_slugs:
    print(
        f"\nFailed to fetch data for {len(failed_slugs)} protocols. Check 'failed_protocols.pkl' for the list."
    )
