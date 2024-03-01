import json
import os
import sys

import duckdb
import simplejson
from tqdm import tqdm

from config.config import CATEGORY_MAPPING

import yaml

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)
    
config = load_config()

json_files_dir = config['data_dir']


def initialize():
    # Append to system path
    sys.path.append("../config")
    # Initialize DuckDB connection
    conn = duckdb.connect()
    return conn

def transform_data(conn):
    # Fetch JSON files from the directory
    json_files = [
        os.path.join(json_files_dir, file)
        for file in os.listdir(json_files_dir)
        if file.endswith(".json")
    ]
    # Split files into chunks
    FILES_PER_CHUNK = 5
    file_chunks = [
        json_files[i : i + FILES_PER_CHUNK]
        for i in range(0, len(json_files), FILES_PER_CHUNK)
    ]

    # Determine all columns from the JSON files
    all_columns = set()
    for file_chunk in tqdm(file_chunks, desc="Processing file chunks"):
        for file in file_chunk:
            with open(file, "r") as f:
                data = json.load(f)
                all_columns.update(
                    data[0].keys() if isinstance(data, list) else data.keys()
                )
    all_columns = sorted(all_columns)
    return file_chunks, all_columns


def get_column_names_from_chunk(file_path):
    """
    Reads a JSON file and returns the set of keys found in the JSON data.
    Assumes the JSON file contains either a list of dictionaries or a single dictionary.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
        # If the data is a list, extract keys from the first item
        if isinstance(data, list) and data:
            return set(data[0].keys())
        # If the data is a dictionary, return its keys
        elif isinstance(data, dict):
            return set(data.keys())
    return set()

def load_data_into_duckdb(conn, file_chunks, all_columns):
    # Create merged table with all columns
    create_table_query = (
        "CREATE TABLE crypto_merged ("
        + ", ".join([f'"{col}" VARCHAR' for col in all_columns])
        + ");"
    )
    conn.execute(create_table_query)

    for file_chunk in tqdm(file_chunks, desc="Inserting data into DuckDB"):
        for file in file_chunk:
            available_columns = get_column_names_from_chunk(file)
            select_columns = ", ".join(
                [
                    f'"{col}"' if col in available_columns else "null"
                    for col in all_columns
                ]
            )
            insert_query = f"INSERT INTO crypto_merged SELECT {select_columns} FROM read_json_auto('{file}', ignore_errors=true, maximum_object_size=150000000);"
            conn.execute(insert_query)


def post_process_data(conn):
    # Load category mapping
    category_to_group_mapping = {
        subcat: maincat
        for maincat, sublist in CATEGORY_MAPPING.items()
        for subcat in sublist
    }
    conn.execute('ALTER TABLE crypto_merged ADD COLUMN "group" VARCHAR;')
    for subcat, maincat in category_to_group_mapping.items():
        conn.execute(
            f"UPDATE crypto_merged SET \"group\" = '{maincat}' WHERE category = '{subcat}';"
        )
    conn.execute("PRAGMA memory_limit='32GB'")
    category_to_type_mapping = {
        subcat: maincat
        for maincat, sublist in CATEGORY_MAPPING.items()
        for subcat in sublist
    }
    conn.execute('ALTER TABLE crypto_merged ADD COLUMN "type" VARCHAR;')
    for category, type_ in category_to_type_mapping.items():
        conn.execute(
            f"UPDATE crypto_merged SET \"type\" = '{type_}' WHERE category = '{category}';"
        )
    conn.execute(
        """UPDATE crypto_merged SET chainTvls = REPLACE(chainTvls, $$'$$, $$"$$);"""
    )

def clean_invalid_chars(json_str):
    """Remove invalid control characters from the JSON string and ensure proper escaping."""
    # Remove control characters
    cleaned_str = json_str.replace("\x00", "")
    # Escape single quotes for SQL compatibility
    cleaned_str = cleaned_str.replace("'", "''")
    return cleaned_str

def cleaning_phase(conn):
    # Fetch all rows from the table
    rows_query = "SELECT id, chainTvls FROM crypto_merged;"
    rows_df = conn.execute(rows_query).fetchdf()

    # Clean rows if necessary
    for _, row in rows_df.iterrows():
        try:
            data = simplejson.loads(row["chainTvls"])
            print(f"ID {row['id']} is clean.")
        except:
            cleaned_chainTvls = clean_invalid_chars(row["chainTvls"])

            update_query = f"UPDATE crypto_merged SET chainTvls = '{cleaned_chainTvls}' WHERE id = {row['id']}"
            conn.execute(update_query)

            try:
                data = simplejson.loads(cleaned_chainTvls)
                print(f"ID {row['id']} cleaned successfully.")
            except:
                print(f"Error in ID {row['id']} after cleaning:")


def save_first_row_to_csv(conn, output_file='first_row.csv'):
    # Fetch the first row from the table
    first_row_query = "SELECT * FROM crypto_merged LIMIT 1;"
    first_row_df = conn.execute(first_row_query).fetchdf()

    # Save the DataFrame to a CSV file
    first_row_df.to_csv(output_file, index=False)
    print(f"First row saved to {output_file}")

def main():
    conn = initialize()
    file_chunks, all_columns = transform_data(conn)
    load_data_into_duckdb(conn, file_chunks, all_columns)
    print("Data loaded into DuckDB.")
    # cleaning_phase(conn)
    # print("Cleaning phase complete.")
    # post_process_data(conn)
    save_first_row_to_csv(conn)



if __name__ == "__main__":
    main()
