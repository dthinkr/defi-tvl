from fastapi import FastAPI, HTTPException, Query, Path, Response
from config.etl_network import ETLNetwork
from config.query import MotherduckClient
from fastapi.responses import HTMLResponse
from config.plot import NetworkVisualizer
from functools import lru_cache


app = FastAPI()

bq = MotherduckClient()
    
etl_network = ETLNetwork(bq=bq)

@app.get("/network-json/{date_input}", summary="Network Data")
async def get_network_json(
    date_input: str = Path(..., description="Date in 'YYYY-MM-DD' format."),
    TOP_X: int = Query(50, description="Number of top connections."),
    granularity: str = Query('daily', description=", 'daily', 'monthly', 'yearly'."),
    mode: str = Query('usd', description="'usd' or 'qty'."),
    type: bool = Query(False, description="Aggregate by type.")

):
    """
    Retrieves network data for a given date with automatic granularity detection.
    """
    try:
        C = bq.compare_periods(date_input, granularity=granularity)
        print(C.head(1))
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
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/protocol-data/{protocol_name}/{granularity}", summary="Protocol Data")
async def protocol_data(protocol_name: str, granularity: str):
    """
    Returns protocol data.
    """
    try:
        df = bq.get_protocol_data(protocol_name, granularity)
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/render-network/{date_input}", summary="Render Network Visualization", response_class=HTMLResponse)
async def render_network(
    date_input: str = Path(..., description="Date in 'YYYY-MM-DD' format."),
    TOP_X: int = Query(50, description="Number of top connections."),
    granularity: str = Query('daily', description=", 'daily', 'monthly', 'yearly'."),
    mode: str = Query('usd', description="'usd' or 'qty'."),
    type: bool = Query(False, description="Aggregate by type.")
):
    """
    Returns an HTML page with a rendered network visualization for a given date.
    """
    try:
        # Directly reuse the get_network_json endpoint
        network_json = await get_network_json(date_input, TOP_X, granularity, mode, type)
        
        # Initialize the NetworkVisualizer
        visualizer = NetworkVisualizer(notebook=False)  # Set notebook to False for web rendering
        
        # Generate the HTML content
        html_content = visualizer.visualize_network(network_json)
        
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/unique-protocols", summary="Unique Protocol Names")
async def unique_protocols():
    """
    Returns a list of unique protocol names from table A.
    """
    try:
        df = bq.get_unique_protocol_names()
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/unique-token-names", summary="Unique Token Names")
async def unique_token_names():
    """
    Returns a list of unique token names from the default table.
    """
    try:
        df = bq.get_unique_token_names()  # No table name passed, uses default
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))