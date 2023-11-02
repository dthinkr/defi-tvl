from google.cloud import bigquery

class BigQueryClient:
    def __init__(self, project, dataset):
        self.client = bigquery.Client()
        self.dataset_ref = self.client.dataset(dataset, project=project)

    def get_table(self, table_name):
        table_ref = self.dataset_ref.table(table_name)
        return self.client.get_table(table_ref)

    def print_table_schema(self, table_name):
        table = self.get_table(table_name)
        for schema_field in table.schema:
            print(f"{schema_field.name}: {schema_field.field_type}")

    def get_sample_dataframe(self, table_name, limit=10):
        query_string = f"SELECT * FROM `{self.dataset_ref.dataset_id}.{table_name}` LIMIT {limit}"
        return self.client.query(query_string).to_dataframe()