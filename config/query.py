from google.cloud import bigquery, exceptions
from google.cloud.bigquery import DatasetReference
from google.cloud.bigquery.table import Table
from google.cloud.bigquery.client import Client
from google.cloud.bigquery.dataset import DatasetReference
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from typing import Optional
import pandas as pd
import streamlit as st
from .config import TABLES, MD_TOKEN
import duckdb

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
        self.dataset_ref: DatasetReference = DatasetReference(project, dataset)

    def _execute_query(self, query: str) -> pd.DataFrame:
        try:
            return self.client.query(query).to_dataframe()
        except exceptions.GoogleCloudError as e:
            raise RuntimeError(f"Query execution failed: {e}")
        
    def _get_date_trunc_expr(self, granularity: str) -> str:
        expressions = {
            'weekly': "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), WEEK(MONDAY))",
            'monthly': "DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))), MONTH)",
            'daily': "DATE(DATE(TIMESTAMP_SECONDS(CAST(ROUND(C.date) AS INT64))))"
        }
        return expressions.get(granularity, expressions['daily'])

    def _get_table(self, table_name: str) -> Table:
        table_ref = self.dataset_ref.table(table_name)
        return self.client._get_table(table_ref) 

    def _get_table_schema(self, table_name: str) -> list:
        """Fetch the table schema"""
        table = self._get_table(table_name)
        return table.schema
    
    def _get_last_modified_time(self, table_name: str) -> str:
        """Get the last modified time of a table."""
        table = self._get_table(table_name)
        last_modified_time = table.modified
        # Convert to a more readable format, if desired
        formatted_time = last_modified_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return formatted_time

    def _get_table_name(self, table_name: str) -> str:
        return f'{self.dataset_ref.dataset_id}.{table_name}'

    def get_dataframe(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        if limit is not None:
            query = (
                f"SELECT * FROM {self._get_table_name(table_name)} LIMIT {limit}"
            )
        else:
            query = (
                f"SELECT * FROM {self._get_table_name(table_name)}"
            )
        return self._execute_query(query)
    
    def get_table_rows(self, table_name, unique_ids):
        """Retrieve entire rows from a specified table based on unique IDs."""
        query = f"""
        SELECT *
        FROM {self._get_table_name(table_name)}
        WHERE id IN ({', '.join(map(str, unique_ids))})
        """
        return self._execute_query(query)
        
    def get_token_distribution(self, token_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve the distribution of a specific token across protocols over time at specified granularity."""

        date_trunc_expr = self._get_date_trunc_expr(granularity)

        query = f"""
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
            {self.dataset_ref.dataset_id}.{TABLES['C']} C
        INNER JOIN 
            {self.dataset_ref.dataset_id}.{TABLES['A']} A ON C.id = A.id
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
        return self._execute_query(query)
    
    def get_protocol_data(self, protocol_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve data for a specific protocol with granularity."""

        date_trunc_expr = self._get_date_trunc_expr(granularity)

        # Construct the SQL query
        query = f"""
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
            {self.dataset_ref.dataset_id}.{TABLES['C']} C
        INNER JOIN 
            {self.dataset_ref.dataset_id}.{TABLES['A']} A ON C.id = A.id
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
        return self._execute_query(query)
    
    def compare_months(self, year1: int, month1: int, year2: int, month2: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Compare monthly aggregated data between two months."""
        query = f"""
        WITH month1_data AS (
            SELECT
                id,
                chain_name,
                token_name,
                DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
                AVG(quantity) AS qty_m1_avg,
                AVG(value_usd) AS usd_m1_avg
            FROM
                {self._get_table_name(table)}
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
                {self._get_table_name(table)}
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
        return self._execute_query(query)
    
    def query_by_month(self, year: int, month: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Query aggregated data by month."""
        # Construct the SQL query
        query = f"""
        SELECT
            id,
            chain_name,
            token_name,
            DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
            AVG(quantity) AS avg_quantity,
            AVG(value_usd) AS avg_value_usd
        FROM
            {self._get_table_name(table)}
        WHERE
            EXTRACT(YEAR FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {year} AND
            EXTRACT(MONTH FROM TIMESTAMP_SECONDS(CAST(date AS INT64))) = {month}
        GROUP BY
            id, chain_name, token_name, year_month
        """
        # Execute the query and return the DataFrame
        return self._execute_query(query)
    
    def get_unique_token_names(self, table: str) -> pd.DataFrame:
        """Fetch unique token names from a specified table."""
        query = f"SELECT DISTINCT token_name FROM {self._get_table_name(table)}"
        try:
            return self._execute_query(query)
        except exceptions.BadRequest as e:
            if 'token_name' in str(e):
                raise ValueError("The column 'token_name' does not exist in the specified table.") from e
            else:
                raise

    def get_token_frequency(self, table: str) -> pd.DataFrame:
        """Retrieve the frequency of each token name from a specified table."""
        query = f"""
        SELECT token_name, COUNT(*) as frequency
        FROM {self._get_table_name(table)}
        GROUP BY token_name
        ORDER BY frequency DESC
        """
        return self._execute_query(query)



class MotherduckClient(BigQueryClient):
    def __init__(self) -> None:
        super().__init__()  # Initialize parent class if needed
        self.client = duckdb.connect(f'md:?motherduck_token={MD_TOKEN}')
        
    def _execute_query(self, query: str) -> pd.DataFrame:
        result = self.client.execute(query).df()
        return result

    def _get_table_name(self, table_name: str) -> str:
        return table_name
    
    def _get_date_trunc_expr(self, granularity: str) -> str:
        """
        Returns the appropriate date truncation expression for DuckDB based on the specified granularity.

        Parameters:
        - granularity (str): The granularity for date truncation, e.g., 'daily', 'weekly', 'monthly'.

        Returns:
        - str: A DuckDB-compatible SQL expression for date truncation.
        """
        if granularity == 'daily':
            return "DATE_TRUNC('day', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')"
        elif granularity == 'weekly':
            return "DATE_TRUNC('week', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')"
        elif granularity == 'monthly':
            return "DATE_TRUNC('month', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')"
        elif granularity == 'yearly':
            return "DATE_TRUNC('year', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')"
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")

    def compare_months(self, year1: int, month1: int, year2: int, month2: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Compare monthly aggregated data between two months."""
        query = f"""WITH month1_data AS (
                SELECT
                    id,
                    chain_name,
                    token_name,
                    DATE_TRUNC('month', TIMESTAMP 'epoch' + date * INTERVAL '1 second') AS year_month,
                    AVG(quantity) AS qty_m1_avg,
                    AVG(value_usd) AS usd_m1_avg
                FROM
                    {self._get_table_name(table)}
                WHERE
                    EXTRACT(YEAR FROM TIMESTAMP 'epoch' + date * INTERVAL '1 second') = {year1} AND
                    EXTRACT(MONTH FROM TIMESTAMP 'epoch' + date * INTERVAL '1 second') = {month1}
                GROUP BY
                    id, chain_name, token_name, year_month
            ),
            month2_data AS (
                SELECT
                    id,
                    chain_name,
                    token_name,
                    DATE_TRUNC('month', TIMESTAMP 'epoch' + date * INTERVAL '1 second') AS year_month,
                    AVG(quantity) AS qty_m2_avg,
                    AVG(value_usd) AS usd_m2_avg
                FROM
                    {self._get_table_name(table)}
                WHERE
                    EXTRACT(YEAR FROM TIMESTAMP 'epoch' + date * INTERVAL '1 second') = {year2} AND
                    EXTRACT(MONTH FROM TIMESTAMP 'epoch' + date * INTERVAL '1 second') = {month2}
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
                m2.usd_m2_avg - m1.usd_m1_avg != 0"""
        
        return self._execute_query(query)
    
    def _get_aggregated_data(self, table_name: str, token_name: str = None, protocol_name: str = None, granularity: str) -> str:
        """
        Returns a SQL query for retrieving aggregated data with averages over a specified period.
        
        Parameters:
        - table_name (str): The name of the table to query.
        - token_name (str): Optional. The name of the token to filter by.
        - protocol_name (str): Optional. The name of the protocol to filter by.
        - granularity (str): The granularity for date truncation, e.g., 'daily', 'weekly', 'monthly'.
        
        Returns:
        - str: A SQL query string.
        """
        date_trunc_expr = self._get_date_trunc_expr(granularity)
        token_filter = f"AND C.token_name = '{token_name}'" if token_name else ""
        protocol_filter = f"AND A.name = '{protocol_name}'" if protocol_name else ""

        query = f"""
        WITH AggregatedData AS (
            SELECT
                {date_trunc_expr} as aggregated_date,
                C.id as id,
                A.name as protocol_name,
                A.category as category,
                A.type as type,
                C.chain_name,
                C.token_name,
                SUM(C.quantity) as sum_quantity,
                SUM(C.value_usd) as sum_value_usd
            FROM 
                {self._get_table_name(table_name)} C
            INNER JOIN 
                {self._get_table_name(TABLES['A'])} A ON C.id = A.id
            WHERE 
                C.quantity > 0 AND
                C.value_usd > 0
                {token_filter}
                {protocol_filter}
            GROUP BY 
                aggregated_date, C.id, A.name, A.category, A.type, C.chain_name, C.token_name
        )
        SELECT
            aggregated_date,
            id,
            protocol_name,
            category,
            type,
            chain_name,
            token_name,
            AVG(sum_quantity) as avg_total_quantity,
            AVG(sum_value_usd) as avg_total_value_usd
        FROM AggregatedData
        GROUP BY
            aggregated_date,
            id,
            protocol_name,
            category,
            type,
            chain_name,
            token_name
        ORDER BY 
            aggregated_date, id
        """
        return query
    
    def get_token_distribution(self, token_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve the distribution of a specific token across protocols over time at specified granularity."""
        query = self._get_aggregated_data(TABLES['C'], token_name=token_name, granularity=granularity)
        return self._execute_query(query)

    def get_protocol_data(self, protocol_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve data for a specific protocol with granularity, calculating the average of sums."""
        query = self._get_aggregated_data(TABLES['C'], protocol_name=protocol_name, granularity=granularity)
        return self._execute_query(query)