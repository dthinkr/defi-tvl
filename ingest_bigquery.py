import requests
import json
import os
import yaml
import pickle
import pandas as pd
import polars as pl
from prefect import task, flow, get_run_logger
from config.config import TABLES, MD_TOKEN, CATEGORY_MAPPING
import duckdb
import asyncio
import psutil
from config.etl_network import ETLNetwork
from config.query import MotherduckClient
from config.plot import save_heatmap
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

########################### PART 1: Llama -> Motherduck
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()
DATA_DIR = config["data_dir"]
BASE_DIR = config["base_dir"]
BASE_URL = config["base_url"]
MAX_SLUGS = config.get("max_slugs", None)

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
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str)
        df["type"] = "default"
        df.to_parquet(PROTOCOL_HEADERS_PARQUET, index=False)
        await upload_df_to_motherduck.fn(PROTOCOL_HEADERS_PARQUET, TABLES["A"])
        await add_type_column.fn()
        os.remove(PROTOCOL_HEADERS_FILE)
        os.remove(PROTOCOL_HEADERS_PARQUET)
    else:
        get_run_logger().info("No data found in the API response.")
    return data


@task
async def add_type_column():
    con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")
    con.execute(
        f"ALTER TABLE {TABLES['A']} ADD COLUMN IF NOT EXISTS type VARCHAR;"
    )

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
    con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")
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
    with open(file_path, "r") as f:
        data = json.load(f)

    results = []
    for chain_name, chain_data in data["chainTvls"].items():
        tokens_usd = chain_data["tokensInUsd"]
        tokens_quantity = chain_data["tokens"]

        for usd_entry, quantity_entry in zip(tokens_usd, tokens_quantity):
            date = usd_entry["date"]
            for token_name, value_usd in usd_entry["tokens"].items():
                quantity = quantity_entry["tokens"].get(token_name, 0)
                # large int handling
                value_usd_str = str(value_usd)
                quantity_str = str(quantity)
                results.append(
                    {
                        "id": data["id"],
                        "chain_name": chain_name,
                        "date": date,
                        "token_name": token_name,
                        "quantity": quantity_str,
                        "value_usd": value_usd_str,
                    }
                )

    df = pl.DataFrame(results)

    # convert large int back
    if "quantity" in df.columns:
        df = df.with_columns(pl.col("quantity").cast(pl.Float64).fill_null(0))
    if "value_usd" in df.columns:
        df = df.with_columns(pl.col("value_usd").cast(pl.Float64).fill_null(0))

    return df


@task
async def process_and_filter_file(
    con, json_file_path, parquet_file_path, latest_dates
):
    df = extract_token_tvl(json_file_path)
    if not df.is_empty():
        df = df.join(
            latest_dates, on=["id", "chain_name", "token_name"], how="left"
        )
        filtered_rows = df.filter(pl.col("date") > pl.col("latest_date"))

        filtered_rows = filtered_rows.drop("latest_date")

        if not filtered_rows.is_empty():
            filtered_rows.write_parquet(parquet_file_path)
            await upload_df_to_motherduck.fn(
                parquet_file_path, TABLES["C"], con
            )
            get_run_logger().warning(
                "Uploading %s lines of new data for %s",
                filtered_rows.shape[0],
                json_file_path,
            )
            os.remove(parquet_file_path)
        else:
            # get_run_logger().warning("No new data to process for %s.", json_file_path)
            pass
    else:
        get_run_logger().critical(
            "No data found in llama data %s.", json_file_path
        )


async def clear_motherduck_table(tables: list, delete_tables: list = None):
    con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")
    if delete_tables is None:
        delete_tables = []

    for table in tables:
        if table in delete_tables:
            con.execute(f"DROP TABLE IF EXISTS {table};")
        else:
            exists = con.execute(
                f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')"
            ).fetchone()[0]
            if exists:
                con.execute(f"DELETE FROM {table};")
    con.close()


@task(retries=3, retry_delay_seconds=[1, 10, 100])
async def upload_df_to_motherduck(
    file_path,
    table_name,
    con=duckdb.connect(f"md:?motherduck_token={MD_TOKEN}"),
):
    exists = con.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}')"
    ).fetchone()[0]

    if not exists:
        con.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')"
        )
    else:
        con.execute(
            f"INSERT INTO {table_name} SELECT * FROM read_parquet('{file_path}')"
        )


@task
async def download_and_process_single_protocol(slug, latest_dates):
    url = f"{BASE_URL}protocol/{slug}"
    data = fetch_data(url)
    if data:
        con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")
        json_file_path = os.path.join(DATA_DIR, f"{slug}.json")
        parquet_file_path = os.path.join(DATA_DIR, f"{slug}.parquet")
        save_data_to_file(data, json_file_path)
        await process_and_filter_file.fn(
            con, json_file_path, parquet_file_path, latest_dates
        )
        os.remove(json_file_path)


@task
async def update_mapping():
    bq = MotherduckClient()
    etl = ETLNetwork(bq=bq)
    etl.update_mapping()


def _get_system_memory_info_gb():
    mem = psutil.virtual_memory()
    return mem.total / (1024.0**3)


def _calculate_concurrent_tasks(
    memory_per_task_gb=20 / 200, safety_factor=config["safety_factor"]
):
    total_memory_gb = _get_system_memory_info_gb()
    usable_memory_gb = total_memory_gb * safety_factor
    max_concurrent_tasks_based_on_memory = int(
        usable_memory_gb / memory_per_task_gb
    )
    return max_concurrent_tasks_based_on_memory


def _generate_and_save_heatmap():
    con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")

    query = """
    SELECT id, strftime('%Y-%m-%d', CAST(to_timestamp(date) AS TIMESTAMP)) AS day, COUNT(*) as entry_count
    FROM {table_name}
    GROUP BY id, day
    ORDER BY day
    """.format(
        table_name=TABLES["C"]
    )
    df = con.execute(query).df()

    df["protocol_rank"] = df["id"].astype("category").cat.codes
    df["entry_present"] = df["entry_count"].apply(lambda x: 1 if x > 0 else 0)
    df["day"] = pd.to_datetime(df["day"])
    pivot_df = df.pivot(
        index="protocol_rank", columns="day", values="entry_present"
    ).fillna(0)

    save_heatmap(pivot_df)


@task
async def _get_latest_dates_for_tokens():
    con = duckdb.connect(f"md:?motherduck_token={MD_TOKEN}")
    query = """
    SELECT id, chain_name, token_name, MAX(date) as latest_date
    FROM {table_name}
    GROUP BY id, chain_name, token_name
    """.format(
        table_name=TABLES["C"]
    )
    df = con.execute(query).fetchdf()
    con.close()
    latest_dates_df = pl.from_pandas(df)
    get_run_logger().info("Fetched latest dates for tokens.")
    return latest_dates_df


@flow
async def ingest_llama_motherduck():
    await clear_motherduck_table(tables=["A"], delete_tables=["A"])
    await download_protocol_headers()
    latest_dates = await _get_latest_dates_for_tokens()

    all_protocol_slugs = get_all_protocol_slugs()[:MAX_SLUGS]
    max_concurrent_tasks = _calculate_concurrent_tasks()
    total_slugs_to_process = (
        len(all_protocol_slugs)
        if MAX_SLUGS is None
        else min(len(all_protocol_slugs), MAX_SLUGS)
    )

    for i in range(0, total_slugs_to_process, max_concurrent_tasks):
        batch_slugs = all_protocol_slugs[i : i + max_concurrent_tasks]
        tasks = [
            download_and_process_single_protocol(slug, latest_dates)
            for slug in batch_slugs
        ]
        await asyncio.gather(*tasks)

    await update_mapping()
    _generate_and_save_heatmap()