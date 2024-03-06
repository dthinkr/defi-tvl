from fastapi import FastAPI, HTTPException, Query, Path
from config.etl_network import ETLNetwork
from config.query import BigQueryClient, MotherduckClient

app = FastAPI()

bq = MotherduckClient()
    
etl_network = ETLNetwork(bq=bq)

@app.get("/network-json/{date_input}", summary="Network Data")
async def get_network_json(
    date_input: str = Path(..., description="Date in 'YYYY-MM-DD' format."),
    TOP_X: int = Query(50, description="Number of top connections."),
    granularity: str = Query('daily', description=", 'daily', 'monthly', 'yearly'."),
    mode: str = Query('usd', description="'usd' or 'qty'."),
    type: str = Query(None, description="Aggregate by type.")

):
    """
    Retrieves network data for a given date with automatic granularity detection.
    """
    try:
        C = bq.compare_periods(date_input, granularity=granularity)
        network_json = etl_network.process_dataframe(C, TOP_X=TOP_X, mode=mode, type=type)
        return network_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token-distribution/{token_name}/{granularity}", summary="Token Distribution")
async def token_distribution(token_name: str, granularity: str):
    """
    Returns token distribution data.
    """
    try:
        df = bq.get_token_distribution(token_name, granularity)
        return df.to_json(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/protocol-data/{protocol_name}/{granularity}", summary="Protocol Data")
async def protocol_data(protocol_name: str, granularity: str):
    """
    Returns protocol data.
    """
    try:
        df = bq.get_protocol_data(protocol_name, granularity)
        return df.to_json(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))