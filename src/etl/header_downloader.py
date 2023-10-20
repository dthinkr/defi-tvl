
# downloader.py
import requests
import json
import os
from config import DATA_DIR

class BaseDownloader:
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename

    def fetch_data(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None

    def save_data_to_file(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)

class ProtocolDownloader(BaseDownloader):
    def __init__(self):
        super().__init__("https://api.llama.fi/protocols", os.path.join(DATA_DIR, "protocol_headers.json"))

if __name__ == "__main__":
    downloader = ProtocolDownloader()
    data = downloader.fetch_data()
    
    if data:
        downloader.save_data_to_file(data)
        print(f"Data saved to {downloader.filename}")
    else:
        print("Failed to fetch data for all protocols.")
