import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import patch
from endpoint import app

client = TestClient(app)

@patch('endpoint.bq.compare_months', return_value='mocked dataframe')
@patch('endpoint.etl_network.process_dataframe', return_value={'data': 'processed'})
def test_get_network_json(mock_compare_months, mock_process_dataframe):
    response = client.get("/network-json/2023-01?TOP_X=10&mode=usd")
    assert response.status_code == 200
    assert response.json() == {'data': 'processed'}

@patch('endpoint.bq.get_token_distribution', return_value=pd.DataFrame([{'mocked': 'dataframe'}]))
def test_token_distribution(mock_get_token_distribution):
    response = client.get("/token-distribution/USDC/monthly")
    assert response.status_code == 200
    assert response.json() != []

@patch('endpoint.bq.get_protocol_data', return_value=pd.DataFrame([{'mocked': 'dataframe'}]))
def test_protocol_data(mock_get_protocol_data):
    response = client.get("/protocol-data/MakerDAO/monthly")
    assert response.status_code == 200
    assert response.json() != []
