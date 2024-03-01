from prefect import flow

if __name__ == "__main__":
    flow.from_source(
    source="https://github.com/dthinkr/defi-tvl.git",
    entrypoint="data_ingest.py:run_data_ingestion",
    ).deploy(
        name="managed_ccaf",
        work_pool_name="ccaf",
    )