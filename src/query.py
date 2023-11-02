import os

from google.cloud import bigquery

from config.config import QUERY_DATA_SET, QUERY_PROJECT

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "private-key.json"


class BigQueryClient:
    def __init__(self, project=QUERY_PROJECT, dataset=QUERY_DATA_SET):
        self.client = bigquery.Client()
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
