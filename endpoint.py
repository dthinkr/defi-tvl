from fastapi import FastAPI, HTTPException
from src.etl_network import ETLNetwork
from config.query import BigQueryClient 
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = FastAPI()

bq = BigQueryClient()
etl_network = ETLNetwork(bq=bq)


@app.get("/network-json/{year_month}")
async def get_network_json(year_month: str, TOP_X: int = 50, mode: str = 'usd'):
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