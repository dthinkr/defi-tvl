from config.config import MD_TOKEN
from prefect import flow, task
from datetime import datetime, timedelta
import requests
import json
import os
import tempfile
import asyncio
import duckdb
import httpx


@task
async def fetch_and_save_json(date_str, base_url, params, temp_dir):
    url = f"{base_url}/network-json/{date_str}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            network_json = response.json()
            filename = os.path.join(temp_dir, f"network_data_{date_str}.json")
            with open(filename, 'w') as f:
                json.dump(network_json, f)
            print(f"Data for {date_str} saved to {filename}")
            return filename
        else:
            print(f"Failed to retrieve data for {date_str}: {response.status_code}")
            return None
        
@task
def upload_to_duckdb(file_path):
    con = duckdb.connect(f'md:tvl_network?motherduck_token={MD_TOKEN}')
    con.execute(f"""CREATE TABLE IF NOT EXISTS network_json AS SELECT * FROM read_json_auto('{file_path}')""")
    print(f"Uploaded {file_path} to DuckDB")

@flow
async def main_flow(start_date, end_date):
    base_url = "http://127.0.0.1:8000"
    params = {
        "TOP_X": None,
        "granularity": "daily",
        "mode": "usd",
        "type": True
    }
    temp_dir = tempfile.mkdtemp()
    
    tasks = []
    current_date = start_date
    while current_date < end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        task = fetch_and_save_json(date_str, base_url, params, temp_dir)
        tasks.append(task)
        current_date += timedelta(days=1)
    
    file_paths = await asyncio.gather(*tasks)
    for file_path in filter(None, file_paths):  # Filter out None values
        upload_to_duckdb(file_path)
    
    # Clean up
    for file_path in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file_path))
    os.rmdir(temp_dir)
    print("Temporary files and directory deleted.")

# Define your start and end dates
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 3, 1)

# Run the flow
asyncio.run(main_flow(start_date, end_date))