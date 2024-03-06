import pytest
from unittest.mock import MagicMock
from config.query import BigQueryClient, MotherduckClient

@pytest.fixture
def bigquery_client():
    client = BigQueryClient()
    client.get_token_distribution = MagicMock(return_value='mocked dataframe')
    client.get_protocol_data = MagicMock(return_value='mocked dataframe')
    client.compare_periods = MagicMock(return_value='mocked dataframe')
    return client

@pytest.fixture
def motherduck_client():
    client = MotherduckClient()
    client.get_token_distribution = MagicMock(return_value='mocked dataframe')
    client.get_protocol_data = MagicMock(return_value='mocked dataframe')
    client.compare_periods = MagicMock(return_value='mocked dataframe')
    return client

def test_get_token_distribution_bigquery(bigquery_client):
    df = bigquery_client.get_token_distribution('USDC', 'monthly')
    assert df == 'mocked dataframe'

def test_get_token_distribution_duckdb(motherduck_client):
    df = motherduck_client.get_token_distribution('USDC', 'monthly')
    assert df == 'mocked dataframe'

def test_get_protocol_data_bigquery(bigquery_client):
    df = bigquery_client.get_protocol_data('MakerDAO', 'monthly')
    assert df == 'mocked dataframe'

def test_get_protocol_data_duckdb(motherduck_client):
    df = motherduck_client.get_protocol_data('MakerDAO', 'monthly')
    assert df == 'mocked dataframe'

def test_compare_periods_bigquery(bigquery_client):
    df = bigquery_client.compare_periods('2023')
    assert df == 'mocked dataframe'

def test_compare_periods_duckdb(motherduck_client):
    df = motherduck_client.compare_periods('2023-01-24', 'monthly')
    assert df == 'mocked dataframe'