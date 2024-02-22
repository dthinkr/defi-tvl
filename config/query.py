from google.cloud import bigquery
from google.cloud.bigquery.table import Table
from google.cloud.bigquery.client import Client
from google.cloud.bigquery.dataset import DatasetReference
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from typing import Optional
import pandas as pd
import streamlit as st
from .config import TABLES

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
    
    def get_table_rows(self, table_name, unique_ids):
        table_name = TABLES[table_name]
        """Retrieve entire rows from a specified table based on unique IDs."""
        query = f"""
        SELECT *
        FROM `{self.dataset_ref.dataset_id}.{table_name}`
        WHERE id IN ({', '.join(map(str, unique_ids))})
        """
        return self.client.query(query).to_dataframe()
        
    def get_token_distribution(self, token_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve the distribution of a specific token across protocols over time at specified granularity."""

        # Helper function to get the SQL expression for date truncation
        def get_date_trunc_expr(granularity):
            if granularity == 'weekly':
                return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), WEEK(MONDAY))"
            elif granularity == 'monthly':
                return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), MONTH)"
            else:  # Default to daily granularity
                return "DATE(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))))"

        # Get the date truncation expression based on the granularity
        date_trunc_expr = get_date_trunc_expr(granularity)

        # Construct the SQL query with aggregation
        query_string = f"""
        SELECT 
            {date_trunc_expr} as aggregated_date,
            C.id as id,
            A.name as protocol_name,
            A.category as category,
            A.type as type,
            C.chain_name,
            SUM(C.quantity) as total_quantity,
            SUM(C.value_usd) as total_value_usd
        FROM 
            `{self.dataset_ref.dataset_id}.{TABLES['C']}` C
        INNER JOIN 
            `{self.dataset_ref.dataset_id}.{TABLES['A']}` A ON C.id = A.id
        WHERE 
            C.token_name = '{token_name}' AND
            C.quantity > 0 AND
            C.value_usd > 0
        GROUP BY 
            aggregated_date,
            id,
            protocol_name,
            category,
            type,
            chain_name
        ORDER BY 
            aggregated_date,
            id
        """

        # Execute query and retrieve data
        df = self.client.query(query_string).to_dataframe()
        latest_date = df['aggregated_date'].max()

        return df
    
    def get_protocol_data(self, protocol_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve data for a specific protocol with granularity."""
        # Helper function for date truncation expression
        def get_date_trunc_expr(granularity):
            if granularity == 'weekly':
                return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), WEEK(MONDAY))"
            elif granularity == 'monthly':
                return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), MONTH)"
            else:  # Default to daily granularity
                return "DATE(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))))"

        # Get the date truncation expression based on the granularity
        date_trunc_expr = get_date_trunc_expr(granularity)

        # Construct the SQL query
        query_string = f"""
        SELECT 
            {date_trunc_expr} as aggregated_date,
            C.id as id,
            A.name as protocol_name,
            A.category as category,
            A.type as type,
            C.chain_name,
            C.token_name,  # Ensure 'token_name' column is included if needed
            SUM(C.quantity) as total_quantity,
            SUM(C.value_usd) as total_value_usd
        FROM 
            `{self.dataset_ref.dataset_id}.{TABLES['C']}` C
        INNER JOIN 
            `{self.dataset_ref.dataset_id}.{TABLES['A']}` A ON C.id = A.id
        WHERE 
            A.name = '{protocol_name}' AND
            C.quantity > 0 AND
            C.value_usd > 0
        GROUP BY 
            aggregated_date,
            id,
            protocol_name,
            category,
            type,
            chain_name,
            token_name  # Include 'token_name' in GROUP BY if it's selected
        ORDER BY 
            aggregated_date,
            id
        """
        return self.client.query(query_string).to_dataframe()

    def get_data_with_type(self, table_name: str, granularity: str) -> pd.DataFrame:
            """Retrieve data from table C with the specified granularity and include 'type' from table A."""
            
            def get_date_trunc_expr(granularity):
                if granularity == 'weekly':
                    return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), WEEK(MONDAY))"
                elif granularity == 'monthly':
                    return "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), MONTH)"
                else:
                    return "DATE(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))))"

            date_trunc_expr = get_date_trunc_expr(granularity)

            query_string = f"""
            SELECT 
                {date_trunc_expr} as aggregated_date,
                C.id,
                A.name as protocol_name,
                A.category,
                A.type,
                C.chain_name,
                C.token_name,
                SUM(C.quantity) as total_quantity,
                SUM(C.value_usd) as total_value_usd
            FROM 
                `{self.dataset_ref.dataset_id}.{TABLES[table_name]}` C
            INNER JOIN 
                `{self.dataset_ref.dataset_id}.{TABLES['A']}` A ON C.id = A.id
            WHERE 
                C.quantity > 0 AND
                C.value_usd > 0
            GROUP BY 
                aggregated_date,
                C.id,
                protocol_name,
                category,
                type,
                chain_name,
                token_name
            ORDER BY 
                aggregated_date,
                C.id
            """

            return self.client.query(query_string).to_dataframe()
    

    def compare_months(self, year1: int, month1: int, year2: int, month2: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Compare monthly aggregated data between two months."""
        query_string = f"""
        WITH month1_data AS (
            SELECT
                id,
                chain_name,
                token_name,
                DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
                AVG(quantity) AS qty_m1_avg,
                AVG(value_usd) AS usd_m1_avg
            FROM
                `{self.dataset_ref.dataset_id}.{table}`
            WHERE
                EXTRACT(YEAR FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {year1} AND
                EXTRACT(MONTH FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {month1}
            GROUP BY
                id, chain_name, token_name, year_month
        ),
        month2_data AS (
            SELECT
                id,
                chain_name,
                token_name,
                DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
                AVG(quantity) AS qty_m2_avg,
                AVG(value_usd) AS usd_m2_avg
            FROM
                `{self.dataset_ref.dataset_id}.{table}`
            WHERE
                EXTRACT(YEAR FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {year2} AND
                EXTRACT(MONTH FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {month2}
            GROUP BY
                id, chain_name, token_name, year_month
        )
        SELECT
            m1.id,
            m1.chain_name,
            m1.token_name,
            m1.year_month AS month1,
            m2.year_month AS month2,
            m1.qty_m1_avg,
            m2.qty_m2_avg,
            m1.usd_m1_avg,
            m2.usd_m2_avg,
            m2.qty_m2_avg - m1.qty_m1_avg AS qty_change,
            m2.usd_m2_avg - m1.usd_m1_avg AS usd_change
        FROM
            month1_data m1
        FULL OUTER JOIN
            month2_data m2 ON m1.id = m2.id AND m1.chain_name = m2.chain_name AND m1.token_name = m2.token_name
        WHERE
            m2.qty_m2_avg - m1.qty_m1_avg != 0 OR
            m2.usd_m2_avg - m1.usd_m1_avg != 0
        """
        return self.client.query(query_string).to_dataframe()
    
    def query_by_month(self, year: int, month: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Query aggregated data by month."""
        # Construct the SQL query
        query_string = f"""
        SELECT
            id,
            chain_name,
            token_name,
            DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
            AVG(quantity) AS avg_quantity,
            AVG(value_usd) AS avg_value_usd
        FROM
            `{self.dataset_ref.dataset_id}.{table}`
        WHERE
            EXTRACT(YEAR FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {year} AND
            EXTRACT(MONTH FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {month}
        GROUP BY
            id, chain_name, token_name, year_month
        """
        # Execute the query and return the DataFrame
        return self.client.query(query_string).to_dataframe()

    
if __name__ == '__main__':
    bq_client = BigQueryClient()
    df = bq_client.get_dataframe('C_protocol_token_tvl', limit=10)
