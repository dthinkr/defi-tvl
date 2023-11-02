import json
import os
import sys

import duckdb
import simplejson
from tqdm import tqdm

from config import CATEGORY_MAPPING, json_files_dir


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
    """Remove invalid control characters from the JSON string."""
    return json_str.replace("\x00", "")


def cleaning_phase(conn):
    # Fetch all rows from the table
    rows_query = "SELECT id, chainTvls FROM crypto_merged;"
    rows_df = conn.execute(rows_query).fetchdf()

    # Clean rows if necessary
    for _, row in rows_df.iterrows():
        try:
            data = simplejson.loads(row["chainTvls"])
        except simplejson.JSONDecodeError:
            cleaned_chainTvls = clean_invalid_chars(row["chainTvls"])

            update_query = f"UPDATE crypto_merged SET chainTvls = '{cleaned_chainTvls}' WHERE id = {row['id']}"
            conn.execute(update_query)

            try:
                data = simplejson.loads(cleaned_chainTvls)
                print(f"ID {row['id']} cleaned successfully.")
            except simplejson.JSONDecodeError as e:
                print(f"Error in ID {row['id']} after cleaning: {e}")


def main():
    conn = initialize()
    file_chunks, all_columns = transform_data(conn)
    load_data_into_duckdb(conn, file_chunks, all_columns)
    cleaning_phase(conn)
    post_process_data(conn)


if __name__ == "__main__":
    main()
