from google.cloud import bigquery
from google.cloud.bigquery.table import Table
from google.cloud.bigquery.client import Client
from google.cloud.bigquery.dataset import DatasetReference
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from typing import Optional
import pandas as pd
import streamlit as st

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import QUERY_DATA_SET, QUERY_PROJECT

class BigQueryClient:
    def __init__(self, project: str = QUERY_PROJECT, dataset: str = QUERY_DATA_SET) -> None:
        self.credentials: Credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        self.client: Client = bigquery.Client(credentials=self.credentials, project=project)
        self.dataset_ref: DatasetReference = self.client.dataset(dataset)

    def get_table(self, table_name: str) -> Table:
        table_ref = self.dataset_ref.table(table_name)
        return self.client.get_table(table_ref)  # Returns a Table object

    def get_table_schema(self, table_name: str) -> list:
        """Fetch the table schema"""
        table = self.get_table(table_name)
        return table.schema  # Returns a list of SchemaField objects

    def get_dataframe(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        if limit is not None:
            query_string = (
                f"SELECT * FROM `{self.dataset_ref.dataset_id}.{table_name}` LIMIT {limit}"
            )
        else:
            query_string = (
                f"SELECT * FROM `{self.dataset_ref.dataset_id}.{table_name}`"
            )
        return self.client.query(query_string).to_dataframe()

if __name__ == '__main__':
    bq_client = BigQueryClient()
    df = bq_client.get_dataframe('C_protocol_token_tvl', limit=10)
    print(df.head())
