from fastapi import FastAPI, HTTPException, Query, Path
from src.etl_network import ETLNetwork
from config.query import BigQueryClient, MotherduckClient
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = FastAPI()

bq = MotherduckClient()
etl_network = ETLNetwork(bq=bq)

@app.get("/network-json/{year_month}", summary="Retrieve Network Data",
         description="Retrieves a JSON representation of the network data for a given month and year, with options to specify the number of top connections and the mode of data representation.")
async def get_network_json(
    year_month: str = Path(..., description="The year and month for which to retrieve network data, in the format 'YYYY-MM'."),
    TOP_X: int = Query(50, description="The number of top connections to include in the network data."),
    mode: str = Query('usd', description="The mode of data representation. Can be 'usd' for United States Dollar value or 'qty' for quantity.")
):
    """
    This endpoint dynamically generates network data based on transactions within the specified month, extending to the next month. It processes the data to map tokens to protocols, adjust transaction flows, and prepare the data for visualization.
    """
    try:
        start_date = datetime.strptime(year_month, "%Y-%m")
        end_date = start_date + relativedelta(months=+1)
        start_year, start_month = start_date.strftime("%Y"), start_date.strftime("%m")
        end_year, end_month = end_date.strftime("%Y"), end_date.strftime("%m")
        
        C = bq.compare_months(start_year, start_month, end_year, end_month)
        
        network_json = etl_network.process_dataframe(C, TOP_X=TOP_X, mode=mode)
        return network_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))