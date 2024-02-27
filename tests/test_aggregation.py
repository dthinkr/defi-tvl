"""this tests whether the granualar data in table C 
    amounts to the aggregated data in table D"""

import pytest
import pandas as pd
from config.query import BigQueryClient
from config.config import TABLES

bq = BigQueryClient()

def get_random_protocol_names(n=5):
    """Fetch a random list of n protocol names from TABLES['A']."""
    query = f"""
    SELECT name
    FROM `{bq.dataset_ref.dataset_id}.{TABLES['A']}`
    ORDER BY RAND()
    LIMIT {n}
    """
    result = bq.client.query(query)
    protocol_names = [row.name for row in result]
    return protocol_names

def get_protocol_id(protocol_name):
    query_protocol_id = f"""
    SELECT id
    FROM `{bq.dataset_ref.dataset_id}.{TABLES['A']}`
    WHERE name = '{protocol_name}'
    """
    protocol_id_result = bq.client.query(query_protocol_id)
    protocol_id = [row.id for row in protocol_id_result][0]  # Assuming the name is unique and always found
    return protocol_id

def get_monthly_avg_from_table_c(protocol_id, year, month):
    formatted_month = month.zfill(2)
    query = f"""
    SELECT
      date,
      chain_name,
      token_name,
      value_usd
    FROM
      `{bq.dataset_ref.dataset_id}.{TABLES['C']}`
    WHERE
      id = {protocol_id} AND
      EXTRACT(YEAR FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {year} AND
      EXTRACT(MONTH FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {int(formatted_month)}
    """
    df = bq.client.query(query).to_dataframe()
    df['date'] = pd.to_datetime(df['date'], unit='s')
    avg_per_token_per_day = df.groupby([df['date'].dt.date, 'chain_name', 'token_name'])['value_usd'].mean().reset_index()
    daily_sum = avg_per_token_per_day.groupby('date')['value_usd'].sum()
    monthly_avg = daily_sum.mean() / 1e9
    return monthly_avg

def get_monthly_avg_from_table_d(protocol_id, year, month):
    formatted_month = month.zfill(2)
    query_avg_liquidity = f"""
    SELECT
      AVG(totalLiquidityUSD) AS avgTotalLiquidityUSD
    FROM
      `{bq.dataset_ref.dataset_id}.{TABLES['D']}`
    WHERE
      id = {protocol_id} AND
      FORMAT_TIMESTAMP('%Y-%m', TIMESTAMP_SECONDS(CAST(date AS INT64))) = '{year}-{formatted_month}'
    """
    avg_liquidity_result = bq.client.query(query_avg_liquidity).to_dataframe()
    avg_liquidity_in_billions = avg_liquidity_result['avgTotalLiquidityUSD'].mean() / 1e9
    return avg_liquidity_in_billions


# Generate test cases dynamically
protocol_names = get_random_protocol_names(n=5)
test_cases = [(name, '2023', '6') for name in protocol_names]


@pytest.mark.parametrize("protocol_name,year,month", test_cases)
def test_aggregation_consistency(protocol_name, year, month):
    protocol_id = get_protocol_id(protocol_name)
    monthly_avg_c = get_monthly_avg_from_table_c(protocol_id, year, month)
    monthly_avg_d = get_monthly_avg_from_table_d(protocol_id, year, month)
    assert abs(monthly_avg_c - monthly_avg_d) < 0.01