import pandas as pd
import streamlit as st
import altair as alt
import numpy as np

from config.config import TABLES
from config.query import BigQueryClient

def load_token_distribution(bq: BigQueryClient, token_name: str, row_percentage: float, granularity: str):
    """Load token distribution data from BigQuery with a percentage and granularity."""
    
    token_distribution_df = bq.get_token_distribution(token_name, row_percentage, granularity)
    
    # Get unique IDs from the token_distribution_df
    unique_ids = token_distribution_df['id'].unique()

    # Retrieve rows from table A based on unique IDs
    table_a_df = bq.get_table_rows('A', unique_ids)
    
    return token_distribution_df, table_a_df

def plot_time_series(data, x_axis, y_axis, color_category):
    # Extract column names from the strings with type annotations
    x_col = x_axis.split(':')[0]
    y_col = y_axis.split(':')[0]
    color_col = color_category.split(':')[0]

    # Step 1: Rank Categories
    category_totals = data.groupby(color_col)[y_col].sum().reset_index()
    category_totals['rank'] = category_totals[y_col].rank(method='max', ascending=False)
    top_categories = category_totals[category_totals['rank'] <= 8][color_col]

    # Step 2: Modify Categories
    data['adjusted_category'] = data.apply(lambda row: row[color_col] if row[color_col] in top_categories.values else 'Other', axis=1)

    # Step 3: Aggregate 'Other' if necessary
    # Note: This step might require adjustments based on the specifics of your data structure.

    # Step 4: Plot
    chart = alt.Chart(data).mark_line().encode(
        x=alt.X(x_axis, axis=alt.Axis(format="%Y-%m")),  # Format x-axis to display year and month
        y=y_axis,
        color=alt.Color('adjusted_category:N')  # Use 'N' to denote nominal (categorical) data
    ).interactive()

    return chart

def main():
    """Execute the Streamlit app."""
    st.title("DeFi TVL: Token Distribution Analysis")
    
    bq = BigQueryClient()

    # Slider for the user to select the percentage of rows to display
    row_percentage = st.slider("Select the percentage of rows to display:", min_value=0, max_value=100, value=100, step=10)
    
    # Selection for the user to define the data granularity
    granularity = st.selectbox("Select data granularity:", options=['daily', 'weekly', 'monthly'], index=1)  # default to 'weekly'

    # User input for selecting a token
    token_name = st.text_input("Enter the token name for analysis (e.g., DAI):", 'USDC')

    if token_name:
        # Fetch data for the specified token name with the user-defined percentage and granularity
        token_distribution_df, table_a_df = load_token_distribution(bq, token_name, row_percentage, granularity)

        if token_distribution_df is not None and not token_distribution_df.empty:
            # Display the DataFrame and the time series plot for the token
            st.write(f"#### Retrieved data has {len(token_distribution_df)} rows")
            st.dataframe(token_distribution_df.head())
            st.write(f"#### Where is {token_name} locked? By protocol")
            ts_chart = plot_time_series(token_distribution_df, 'aggregated_date:T', 'total_value_usd:Q', 'protocol_name:N')
            st.altair_chart(ts_chart, use_container_width=True)
        
            # Dropdown for the user to select the aggregation attribute based on table A columns
            if table_a_df is not None and not table_a_df.empty:
                aggregation_attribute = st.selectbox("Select an attribute from Table A for grouping:", 
                                                     options=table_a_df.columns.tolist(), 
                                                     index=table_a_df.columns.tolist().index('category') 
                                                     if 'category' in table_a_df.columns.tolist() else 0)                
                merged_df = pd.merge(token_distribution_df, table_a_df[['id', aggregation_attribute]], on='id')

                # Merge the two dataframes on the common id ('id')
                merged_df = pd.merge(token_distribution_df, table_a_df[['id', aggregation_attribute]], on='id')

                # Group by the selected attribute and date, and then sum up the total value
                merged_agg = merged_df.groupby([aggregation_attribute, 'aggregated_date']).sum().reset_index()

                st.write(f"#### Where is {token_name} locked? By {aggregation_attribute}")
                ts_chart_a = plot_time_series(merged_agg, 'aggregated_date:T', 'total_value_usd:Q', f'{aggregation_attribute}:N')
                st.altair_chart(ts_chart_a, use_container_width=True)
        else:
            st.write("No data available for the specified token.")


if __name__ == "__main__":
    main()