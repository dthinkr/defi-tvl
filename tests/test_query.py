import pytest
from unittest.mock import patch, MagicMock
from config.query import BigQueryClient, MotherduckClient

# Mock for pandas DataFrame
mock_df = MagicMock()

@pytest.fixture
def bigquery_client():
    with patch('config.query.bigquery.Client') as mock_client:
        mock_client.return_value.query.return_value.to_dataframe.return_value = mock_df
        yield BigQueryClient(project='test_project', dataset='test_dataset')

@pytest.fixture
def motherduck_client():
    with patch('config.query.duckdb.connect') as mock_connect:
        mock_connect.return_value.execute.return_value.fetchall.return_value = [('row1', 'row2')]
        yield MotherduckClient()

def test_bigquery_get_dataframe(bigquery_client):
    df = bigquery_client.get_dataframe('test_table', limit=10)
    assert df == mock_df
    bigquery_client.client.query.assert_called_once()

def test_motherduck_get_dataframe(motherduck_client):
    df = motherduck_client.get_dataframe('test_table', limit=10)
    assert not df.empty
    motherduck_client.client.execute.assert_called_once()