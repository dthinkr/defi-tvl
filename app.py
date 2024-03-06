import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 300
from config.plot_governance import TokenDistributionVisualizer

import pandas as pd
import streamlit as st

import altair as alt
from streamlit_observable import observable

import numpy as np
import itertools

from config.config import CUSTOM_COLORS, TOP_N, original_names, abbreviated_names, TABLES, NETWORK_PRELIMINARIES
from config.query import BigQueryClient, MotherduckClient
from config.chord import ChordDiagramData
from config.plot_network import NetworkVisualizer

import subprocess
import requests
from datetime import datetime, timedelta
import socket
from config.etl_network import ETLNetwork


def start_uvicorn():
    uvicorn_command = "python -m uvicorn endpoint:app --host 0.0.0.0 --port 8000"
    subprocess.Popen(uvicorn_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def is_uvicorn_running():
    return is_port_in_use(8000)

@st.cache_data
def get_network_data(year_month, TOP_X=50, granularity='daily', mode='usd'):
    url = f"http://127.0.0.1:8000/network-json/{year_month}?TOP_X={TOP_X}&granularity={granularity}&mode={mode}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to retrieve network data")
        return None

@st.cache_data
def display_network(network_json):
    unique_categories = set(node['category'] for node in network_json['nodes'])
    color_cycle = itertools.cycle(CUSTOM_COLORS)    
    category_colors = {category: next(color_cycle) for category in unique_categories}

    visualizer = NetworkVisualizer()
    # display_color_legend(category_colors)
    return visualizer.visualize_network(network_json, category_colors)


# The display_color_legend function remains unchanged
def display_color_legend(category_colors):
    raise NotImplementedError("Too many categories identified. Needs to change logic.")
    st.write("## Color Legend for Nodes:")
    st.write(category_colors)
    for category, color in category_colors.items():
        st.markdown(f"- ![{category}](https://via.placeholder.com/15/{color[1:]}/000000?text=+) `{category}`", unsafe_allow_html=True)

@st.cache_data
def load_token_distribution(_bq: BigQueryClient, token_name: str, granularity: str):
    """Load token distribution data from BigQuery with a percentage and granularity."""
    
    token_distribution_df = _bq.get_token_distribution(token_name, granularity)
    
    # Get unique IDs from the token_distribution_df
    unique_ids = token_distribution_df['id'].unique()

    # Retrieve rows from table A based on unique IDs
    table_a_df = _bq.get_table_rows(TABLES['A'], unique_ids)
    
    return token_distribution_df, table_a_df

@st.cache_data
def load_protocol_data(_bq: BigQueryClient, protocol_name: str, granularity: str):
    """Load protocol data from BigQuery based on the protocol name and granularity."""
    return _bq.get_protocol_data(protocol_name, granularity)

# @st.cache_resource
def get_chord_and_day_data(file_path):
    # Create an instance of ChordDiagramData
    chord_data = ChordDiagramData(file_path)

    # Reverse the list of dates
    unique_dates_reversed = list(reversed(chord_data.unique_dates))

    # Get the data for the latest day
    day_data = chord_data.get_data_for_day(unique_dates_reversed[0])

    return chord_data, unique_dates_reversed, day_data

@st.cache_resource
def plot_time_series(data, x_axis, y_axis, color_category):

    x_col = x_axis.split(':')[0]
    y_col = y_axis.split(':')[0]
    color_col = color_category.split(':')[0]

    # Calculate the total and normalized values for stacking
    y_total_col = f"total_{y_col}"
    data[y_total_col] = data.groupby(x_col)[y_col].transform('sum')
    data['normalized_y'] = (data[y_col] / data[y_total_col]) * 100

    # Rank Categories
    category_totals = data.groupby(color_col)[y_col].sum().reset_index()
    category_totals['rank'] = category_totals[y_col].rank(method='max', ascending=False)
    top_categories = category_totals[category_totals['rank'] <= TOP_N][color_col]

    # Modify Categories
    data['adjusted_category'] = data.apply(lambda row: row[color_col] if row[color_col] in top_categories.values else 'Other', axis=1)
    # Original Line Chart
    line_chart = alt.Chart(data).mark_line().encode(
        x=alt.X(x_axis, axis=alt.Axis(format="%Y-%m")),
        y=y_axis,
        color='adjusted_category:N'
    ).interactive()

    # Calculate Percentages for Stacked Area Chart
    y_total_col = f"total_{y_col}"
    data[y_total_col] = data.groupby(x_col)[y_col].transform('sum')
    data['normalized_y'] = (data[y_col] / data[y_total_col]) * 100

    # Stacked Area Chart
    area_chart = alt.Chart(data).mark_area().encode(
        x=alt.X(x_axis, axis=alt.Axis(format="%Y-%m")),
        y=alt.Y('normalized_y:Q', stack='normalize', axis=alt.Axis(format='%')),
        color='adjusted_category:N'
    ).interactive()

    # Combine the charts horizontally
    combined_charts = alt.vconcat(line_chart, area_chart).resolve_legend(
        color='independent'
    )

    return combined_charts

@st.cache_data
def retrieve_table_A(_bq: BigQueryClient):
    """Retrieve table A from BigQuery."""
    return _bq.get_dataframe(TABLES['A'])

@st.cache_data
def table_C_compare_periods(_bq: BigQueryClient, year1, month1, year2, month2):
    C = _bq.compare_periods(year1, month1, year2, month2)
    return C

def main():
    """Execute the Streamlit app."""
    st.title("dFMI TVL Demo")

    if not is_uvicorn_running():
        start_uvicorn()

    st.write("# Network Diagram")
    st.write("This shows the global monthly token locked changes across all DeFi protocols")

    # Define the range of months for the slider

    # User selects the granularity
    granularity_options = ['daily', 'monthly', 'yearly']
    granularity = st.selectbox("Select the granularity:", options=granularity_options, index=0)
    # Define the start and end dates
    start_date = datetime(2020, 1, 1)
    end_date = datetime.now()

    # Generate date range based on selected granularity
    if granularity == 'daily':
        freq = 'D'
    elif granularity == 'monthly':
        freq = 'MS'  # Month start frequency
    elif granularity == 'yearly':
        freq = 'YS'  # Year start frequency

    date_range = pd.date_range(start_date, end_date, freq=freq)

    # Convert date_range to list of strings for display
    if granularity == 'yearly':
        options = [date.strftime("%Y") for date in date_range]
    else:
        options = [date.strftime("%Y-%m-%d") if granularity == 'daily' else date.strftime("%Y-%m") for date in date_range]

    # Create a slider for date selection
    selected_date = st.select_slider(f"Select {granularity.capitalize()}:", options=options, value=options[-1])

    top_x = st.number_input("Select the number of nodes shown, the rest are aggregated:", min_value=1, max_value=500, value=30, step=10)
    mode_options = ['usd', 'qty']
    selected_mode = st.selectbox("Display token amount or token USD value:", options=mode_options, index=0)  # Default to 'usd'
    

    # Fetch the network data for the selected month
    network_data = get_network_data(selected_date, TOP_X=top_x, granularity = granularity, mode=selected_mode)
    # unique_ids = len(set(item['id'] for item in network_data['nodes']))
    # total_size = sum(item['size'] for item in network_data['nodes'])

    # if total_size >= 1e9:
    #     size_in_b_or_m = f"{int(total_size / 1e9)} billion"
    # elif total_size >= 1e6:
    #     size_in_b_or_m = f"{int(total_size / 1e6)} million"
    # else:
    #     size_in_b_or_m = f"{int(total_size)}"  # Less than a million, keep as is

    
    # st.write('## Network Summary')
    # st.write(f'Total nodes: {unique_ids}, Total size: {size_in_b_or_m} USD')


    st.write('## Network Visualization')
    if network_data:
        # Display the network visualization
        html_content = display_network(network_data)
        st.components.v1.html(html_content, height=750, scrolling=True)

    st.write(NETWORK_PRELIMINARIES)

if __name__ == "__main__":
    main()
