import pytest
from config.query import BigQueryClient
from src.etl_network import ETLNetwork

bq = BigQueryClient()
etl = ETLNetwork(bq)

C = bq.compare_months('2023','06','2023','07')


res = etl.process_dataframe(C)

print(res)