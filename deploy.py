from prefect import flow

if __name__ == "__main__":
    flow.from_source(
    source="https://github.com/dthinkr/defi-tvl.git",
    entrypoint="ingest.py:llama_ingest",
    ).deploy(
        name="managed_ccaf",
        work_pool_name="ccaf",
    )