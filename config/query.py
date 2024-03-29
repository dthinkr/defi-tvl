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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

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
    
    def compare_periods(self, year1: int, month1: int, year2: int, month2: int, table: str = TABLES['C']) -> pd.DataFrame:
        """Compare monthly aggregated data between two months."""
        query = f"""
        WITH month1_data AS (
            SELECT
                id,
                chain_name,
                token_name,
                DATE_TRUNC(DATE(TIMESTAMP_SECONDS(CAST(ROUND(date) AS INT64))), MONTH) AS year_month,
                AVG(quantity) AS qty,
                AVG(value_usd) AS usd
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
            m1.qty,
            m2.qty_m2_avg,
            m1.usd,
            m2.usd_m2_avg,
            m2.qty_m2_avg - m1.qty AS qty_change,
            m2.usd_m2_avg - m1.usd AS usd_change
        FROM
            month1_data m1
        FULL OUTER JOIN
            month2_data m2 ON m1.id = m2.id AND m1.chain_name = m2.chain_name AND m1.token_name = m2.token_name
        WHERE
            m2.qty_m2_avg - m1.qty != 0 OR
            m2.usd_m2_avg - m1.usd != 0
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
    
    def get_unique_token_names(self, table: str = TABLES['C']) -> pd.DataFrame:
        """Fetch unique token names from a specified table."""
        table = self._get_table_name(TABLES['C'])
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
    
    def get_unique_protocol_names(self) -> pd.DataFrame:
        """Fetch unique protocol names from table A, ranked by market cap (mcap)."""
        table_name = self._get_table_name(TABLES['A'])
        # Adjust the query to order by mcap in descending order and include the mcap column
        query = f"SELECT DISTINCT name, mcap FROM {self._get_table_name(table_name)} ORDER BY mcap DESC"
        try:
            return self._execute_query(query)
        except exceptions.BadRequest as e:
            if 'name' in str(e) or 'mcap' in str(e):
                raise ValueError("Error in querying table A: " + str(e)) from e
            else:
                raise

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
        expressions = {
            'daily': "DATE_TRUNC('day', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')",
            'weekly': "DATE_TRUNC('week', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')",
            'monthly': "DATE_TRUNC('month', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')",
            'yearly': "DATE_TRUNC('year', TIMESTAMP 'epoch' + C.date * INTERVAL '1 second')"
        }
        return expressions.get(granularity, f"Unsupported granularity: {granularity}")
    
    def compare_periods(self, input_date: str, granularity: str) -> pd.DataFrame:
        """TODO: NEEDS FIXING. LOSES MOST TOKEN DATA FOR UNKNOWN REASON. 
                    NEED TO CHECK AGGREGATE FUNCTION FIRST."""

        parsed_date = parse(input_date)
        start_date = datetime(parsed_date.year, parsed_date.month, parsed_date.day)

        if granularity == 'yearly':
            end_date = start_date + relativedelta(years=1)
        elif granularity == 'monthly':
            end_date = start_date + relativedelta(months=1)
        elif granularity == 'weekly':
            end_date = start_date + relativedelta(days=7)
        elif granularity == 'daily':
            end_date = start_date + relativedelta(days=1)
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")
        
        # Format dates as strings for use in queries
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        
        """TODO: DOES NOT WORK FOR WEEKLY GRANULARITY. """
        query = self._get_aggregated_data(TABLES['C'], granularity, start_date=start_date, end_date=end_date, edge_dates_only=True)
        df = self._execute_query(query)

        df.sort_values(by=['id', 'chain_name', 'token_name', 'aggregated_date'], inplace=True)

        # Calculate changes across the period
        df['usd_change'] = df.groupby(['id', 'chain_name', 'token_name'])['usd'].diff()
        df['qty_change'] = df.groupby(['id', 'chain_name', 'token_name'])['qty'].diff()

        # Isolate start date values and prepare for merging, including aggregated_date
        start_date_df = df[df['aggregated_date'] == start_date][['id', 'chain_name', 'token_name', 'usd', 'qty', 'aggregated_date']].copy()
        start_date_df.rename(columns={'usd': 'start_usd', 'qty': 'start_qty', 'aggregated_date': 'start_date'}, inplace=True)

        # Merge start date values with changes
        df_final = pd.merge(df, start_date_df, on=['id', 'chain_name', 'token_name'], how='left')

        # Filter to keep only rows with changes
        df_final = df_final.dropna(subset=['usd_change', 'qty_change'])

        # Replace original qty, usd, and aggregated_date with start date values
        df_final['usd'] = df_final['start_usd']
        df_final['qty'] = df_final['start_qty']
        df_final['aggregated_date'] = df_final['start_date']

        # Drop the temporary columns used for merging
        df_final.drop(['start_usd', 'start_qty', 'start_date'], axis=1, inplace=True)

        return df_final
    
    def _get_aggregated_data(self, table_name: str, granularity: str, token_name: str = None, protocol_name: str = None, start_date: str = None, end_date: str = None, edge_dates_only: bool = False) -> str:
        from datetime import datetime
        date_trunc_expr = self._get_date_trunc_expr(granularity)
        token_filter = f"AND C.token_name = '{token_name}'" if token_name else ""
        protocol_filter = f"AND A.name = '{protocol_name}'" if protocol_name else ""
        date_filter = ""
        if start_date and end_date:
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
            if edge_dates_only:
                date_filter = f"AND CAST(C.date AS BIGINT) IN ({start_timestamp}, {end_timestamp})"
            else:
                date_filter = f"AND CAST(C.date AS BIGINT) BETWEEN {start_timestamp} AND {end_timestamp}"

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
                C.quantity,
                C.value_usd
            FROM 
                {self._get_table_name(table_name)} C
            INNER JOIN 
                {self._get_table_name(TABLES['A'])} A ON C.id = A.id
            WHERE 
                C.quantity > 0 AND
                C.value_usd > 0
                {token_filter}
                {protocol_filter}
                {date_filter}
        )
        SELECT
            aggregated_date,
            id,
            protocol_name,
            category,
            type,
            chain_name,
            token_name,
            AVG(quantity) as qty,
            AVG(value_usd) as usd
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
        query = self._get_aggregated_data(TABLES['C'], granularity=granularity, token_name=token_name)
        return self._execute_query(query)

    def get_protocol_data(self, protocol_name: str, granularity: str) -> pd.DataFrame:
        """Retrieve data for a specific protocol with granularity, calculating the average of sums."""
        query = self._get_aggregated_data(TABLES['C'], granularity=granularity, protocol_name=protocol_name)
        return self._execute_query(query)
    
