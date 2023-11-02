from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st

from config.config import QUERY_DATA_SET, QUERY_PROJECT

class BigQueryClient:
    def __init__(self, project=QUERY_PROJECT, dataset=QUERY_DATA_SET):
        self.credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
            )
        self.client = bigquery.Client(credentials=self.credentials)
        self.dataset_ref = self.client.dataset(dataset, project=project)

    def get_table(self, table_name):
        table_ref = self.dataset_ref.table(table_name)
        return self.client.get_table(table_ref)

    def get_table_schema(self, table_name):
        """Fetch the table schema"""
        table = self.get_table(table_name)
        return table.schema

    def get_sample_dataframe(self, table_name, limit=10):
        query_string = (
            f"SELECT * FROM `{self.dataset_ref.dataset_id}.{table_name}` LIMIT {limit}"
        )
        return self.client.query(query_string).to_dataframe()