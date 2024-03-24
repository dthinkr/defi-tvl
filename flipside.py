import marimo

__generated_with = "0.3.1"
app = marimo.App()


@app.cell
def __():
    from flipside import Flipside
    import os
    import yaml

    # Load the YAML file to get the API key
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    # Extract the Flipside API key
    flipside_api_key = config['FLIPSIDE_API_KEY']

    # Initialize `Flipside` with your API Key and API Url
    flipside = Flipside(flipside_api_key, "https://api-v2.flipsidecrypto.xyz")

    sql = """
    SELECT 
         platform,
         sum(amount_in_usd) as usd_volume
    FROM ethereum.defi.ez_dex_swaps 
    WHERE platform IN ('uniswap-v3', 'curve')
         -- Wrapped Ether
     AND (token_in = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
         OR 
         token_out = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
         )
     AND block_timestamp >= current_date - 30
    GROUP BY platform
    ORDER BY usd_volume DESC;
    """

    # Run the query against Flipside's query engine and await the results
    query_result_set = flipside.query(sql)
    return (
        Flipside,
        config,
        file,
        flipside,
        flipside_api_key,
        os,
        query_result_set,
        sql,
        yaml,
    )


@app.cell
def __(query_result_set):
    import pandas as pd

    # Convert the query result set to a DataFrame
    df = pd.DataFrame(query_result_set.records)
    return df, pd


@app.cell
def __(df):
    import marimo as mo 
    mo.ui.table(df)
    return mo,


if __name__ == "__main__":
    app.run()
