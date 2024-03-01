import json
import os
import sys
import duckdb
import yaml
from tqdm import tqdm
from config.config import CATEGORY_MAPPING

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)
    
config = load_config()
json_files_dir = config['data_dir']

def initialize():
    sys.path.append("../config")
    conn = duckdb.connect()
    return conn

def transform_data(conn):
    json_files = [os.path.join(json_files_dir, file) for file in os.listdir(json_files_dir) if file.endswith(".json")]
    FILES_PER_CHUNK = 5
    file_chunks = [json_files[i : i + FILES_PER_CHUNK] for i in range(0, len(json_files), FILES_PER_CHUNK)]
    all_columns = set()
    for file_chunk in tqdm(file_chunks, desc="Processing file chunks"):
        for file in file_chunk:
            with open(file, "r") as f:
                data = json.load(f)
                all_columns.update(data[0].keys() if isinstance(data, list) else data.keys())
    all_columns = sorted(all_columns)
    return file_chunks, all_columns

def get_column_names_from_chunk(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        if isinstance(data, list) and data:
            return set(data[0].keys())
        elif isinstance(data, dict):
            return set(data.keys())
    return set()

def load_data_into_duckdb(conn, file_chunks, all_columns):
    create_table_query = "CREATE TABLE crypto_merged (" + ", ".join([f'"{col}" VARCHAR' for col in all_columns]) + ");"
    conn.execute(create_table_query)
    for file_chunk in tqdm(file_chunks, desc="Inserting data into DuckDB"):
        for file in file_chunk:
            available_columns = get_column_names_from_chunk(file)
            select_columns = ", ".join([f'"{col}"' if col in available_columns else "null" for col in all_columns])
            insert_query = f"INSERT INTO crypto_merged SELECT {select_columns} FROM read_json_auto('{file}', ignore_errors=true, maximum_object_size=150000000);"
            conn.execute(insert_query)

def main():
    conn = initialize()
    file_chunks, all_columns = transform_data(conn)
    load_data_into_duckdb(conn, file_chunks, all_columns)
    df = conn.execute('SELECT * FROM crypto_merged;').fetchdf()
    df.to_parquet('crypto_merged.parquet')
    print("Data loaded into DuckDB.")

if __name__ == "__main__":
    main()