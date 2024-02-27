import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 300
from config.plot_governance import TokenDistributionVisualizer

import pandas as pd
import streamlit as st

import altair as alt
from streamlit_observable import observable

import numpy as np
import itertools as itertools

from config.config import TOP_N, original_names, abbreviated_names, TABLES
from config.query import BigQueryClient
from config.chord import ChordDiagramData
from config.plot_network import NetworkVisualizer

from datetime import datetime, timedelta

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
def table_C_compare_months(_bq: BigQueryClient, year1, month1, year2, month2):
    C = _bq.compare_months(year1, month1, year2, month2)
    return C

def main():
    """Execute the Streamlit app."""
    st.title("dFMI TVL Demo")

    # # Plotting section
    # st.write("# Token Distribution Visualization")

    # # Create an instance of the visualization class
    # visualizer = TokenDistributionVisualizer('data/tvl/aave_agg.csv', 'tab10')

    # # Calculate Gini coefficients
    # visualizer.calculate_gini_coefficients()

    # # Display Gini Coefficient Plot
    # st.write("## Gini Coefficient Over Time")
    # visualizer.plot_gini_coefficients()
    # st.pyplot(plt)

    # # Display Staked Tokens Plot
    # st.write("## Staked Tokens Over Time")
    # visualizer.aggregate_top_addresses()
    # visualizer.plot_staked_tokens()
    # st.pyplot(plt)

    # # Display Yearly Distribution Plot
    # st.write("## Yearly Token Distribution")
    # visualizer.plot_yearly_distribution()
    # st.pyplot(plt)

    bq = BigQueryClient()

    tab1, tab2, tab3 = st.tabs(['Token Analysis', 'Chord Diagram', 'Network Diagram'])

    with tab1: 

        st.write("# Token Analysis")

        granularity = st.selectbox("Select data granularity:", options=['daily', 'weekly', 'monthly'], index=2)  # default to 'weekly'

        # User input for selecting a token
        token_name = st.text_input("Enter the token name for analysis (e.g., DAI):", 'USDC')
        
        if token_name:
            # Fetch data for the specified token name with the user-defined percentage and granularity
            token_distribution_df, table_a_df = load_token_distribution(bq, token_name, granularity)

            token_distribution_df['aggregated_date'] = pd.to_datetime(token_distribution_df['aggregated_date'])
            token_distribution_df['aggregated_date'] = token_distribution_df['aggregated_date'].dt.strftime('%Y-%m-%d')

            # token_distribution_df.to_csv(f'distribution {token_name}.csv', index=False)

            # Convert DataFrame to JSON-serializable format (list of dictionaries)
            data_for_observable = token_distribution_df.to_dict(orient='records')

            st.write(f'## Where is {token_name} locked?')
            # st.write('### Tree map')
            # st.write('Moved to design improvements')
            # # Pass this data to the Observable component
            # # observable("Tree", 
            # #         notebook="@venvox-ws/defi-tvl-data-loading", 
            # #         targets=["area"],
            # #         redefine={"data": data_for_observable,})
            
            extracted_df = token_distribution_df[['aggregated_date', 'protocol_name', 'type', 'total_value_usd']]
            extracted_df.columns = ['date', 'name', 'category', 'value']
            extracted_df.loc[:, 'value'] = (extracted_df['value'] / 1000000).astype(int)

            # Convert 'date' to datetime and filter out dates before 2021-01-01
            extracted_df.loc[:, 'date'] = pd.to_datetime(extracted_df['date'])
            extracted_df = extracted_df[extracted_df['date'] >= pd.to_datetime('2021-01-01')]
            
            # Adjust all dates to the first day of their respective months
            extracted_df['date'] = extracted_df['date'].apply(lambda x: x.replace(day=1))

            extracted_df = extracted_df.groupby(['date', 'name', 'category'], as_index=False).sum()

            # Convert 'date' back to string
            extracted_df['date'] = extracted_df['date'].dt.strftime('%Y-%m-%d')

            # Convert the DataFrame to a dictionary
            extracted_df = extracted_df.to_dict(orient='records')

            # st.write('### Bar Chart Race')

            # # Pass this data to the Observable component
            # observable("Race", 
            #         notebook="@venvox-ws/bar-chart-race", 
            #         targets=["chart"],
            #         redefine={"data2": extracted_df,})
            
            st.write('### Time Series')
            
            # Dropdown for the user to select the aggregation attribute based on table A columns
            if table_a_df is not None and not table_a_df.empty:
                aggregation_attribute = st.selectbox("Select an attribute from Table A for grouping:", 
                                                    options=table_a_df.columns.tolist(), 
                                                    index=table_a_df.columns.tolist().index('type') 
                                                    if 'category' in table_a_df.columns.tolist() else 0)

                # Merge the two dataframes on the common 'id', adding suffixes to distinguish columns with the same name
                merged_df = pd.merge(token_distribution_df, table_a_df[['id', aggregation_attribute]], on='id', suffixes=('_token', '_a'))

                # Handle renamed columns if 'aggregation_attribute' exists in both DataFrames
                if aggregation_attribute in token_distribution_df.columns:
                    aggregation_attribute += '_a'  # Use the suffix to refer to the column from table_a_df

                # Group by the selected attribute and date, and then sum up the total value
                merged_agg = merged_df.groupby([aggregation_attribute, 'aggregated_date']).sum(numeric_only=True).reset_index()

                st.write(f"#### Where is {token_name} locked? Aggregated by {aggregation_attribute}")
                ts_chart_a = plot_time_series(merged_agg, 'aggregated_date:T', 'total_value_usd:Q', f'{aggregation_attribute}:N')
                st.altair_chart(ts_chart_a, use_container_width=True)

            else:
                st.write("No data available for the specified token.")

        st.write("# Protocol Analysis")
        # User input for selecting a protocol
        protocol_name = st.text_input("Enter the protocol name for analysis:", 'MakerDAO')

        if protocol_name:
            # Fetch data for the specified protocol using the cached function
            protocol_data_df = load_protocol_data(bq, protocol_name, granularity)

            if protocol_data_df is not None and not protocol_data_df.empty:
                # Code to process and plot the data
                st.write(f"#### Token Distribution in {protocol_name} Protocol")
                ts_chart = plot_time_series(protocol_data_df, 'aggregated_date:T', 'total_value_usd:Q', 'token_name:N')
                st.altair_chart(ts_chart, use_container_width=True)
            else:
                st.write("No data available for the specified protocol.")

    # with tab2: 
    #     st.write("# Chord Diagram: Inter-Protocol Locked Values")
    #     st.write("## Temp Removed, Improving Performance")
    #     # chord_data, unique_dates_reversed, day_data = get_chord_and_day_data('data/tvl/db/tb.parquet')
        
    #     # # Dropdown to select a specific date, defaulting to the first (latest) date
    #     # selected_date = st.selectbox("Select a date:", options=unique_dates_reversed, index=0)

    #     # # If selected date is not the latest, get data for the selected date
    #     # if selected_date != unique_dates_reversed[0]:
    #     #     day_data = chord_data.get_data_for_day(selected_date)

    #     # day_data["names"] = abbreviated_names
    #     # observable("Chord", 
    #     #         notebook="@venvox-ws/chord-diagram", 
    #     #         targets=["chart"],
    #     #         redefine={"data": day_data})
    
    # long_markdown = """
    #                 ### Preliminaries

    #                 Let:

    #                 - $\mathcal{A}$ represent the set of all protocols, where each protocol $a \in \mathcal{A}$ is identified by a unique identifier $id_a$, and may have associated attributes such as name and URL.
    #                 - $\mathcal{C}$ denote the set of time-based data entries, where each entry $c \in \mathcal{C}$ corresponds to a token and includes information on the token's name, the change in its locked value over a specified time interval, and possibly its association with a protocol in $\mathcal{A}$.

    #                 ### Categorization Function

    #                 Define a categorization function $\phi: \mathcal{C} \\rightarrow \mathcal{K}$, which maps each token $c$ to a category $k \in \mathcal{K} = \{ rev\_map, LP, UNKNOWN, Other \}$ based on predefined rules related to the token's name and presence in reverse mappings or lists.

    #                 ### Processing Functions

    #                 1. **Unknown Tokens Processing** $\psi_{UNKNOWN}: \mathcal{C}_{UNKNOWN} \\rightarrow \mathcal{A}$: For tokens categorized as UNKNOWN, this function attempts to match token names to Ethereum addresses and subsequently to protocol identifiers in $\mathcal{A}$, effectively refining $\mathcal{C}_{UNKNOWN}$ to a more identifiable subset of $\mathcal{A}$.

    #                 2. **Other Tokens Processing** $\psi_{Other}: \mathcal{C}_{Other} \\rightarrow \mathcal{A} \cup \{ null \}$: Applies manual mappings and filters to tokens in the Other category, potentially mapping them to protocols in $\mathcal{A}$ or excluding them (mapped to null).

    #                 3. **Reverse Mapping Application** $\psi_{rev\_map}: \mathcal{C}_{rev\_map} \\rightarrow \mathcal{A}$: Directly maps tokens in the rev_map category to protocols in $\mathcal{A}$ using the provided reverse mapping.

    #                 ### Merging and Sorting

    #                 After processing, the subsets of $\mathcal{C}$ are merged into a single set $\mathcal{C}_{merged}$, which is then sorted based on the magnitude of value change, resulting in $\mathcal{C}_{sorted}$.

    #                 ### Graph Construction

    #                 Construct a directed graph $G = (V, E)$ where:

    #                 - $V$ corresponds to protocols in $\mathcal{A}$, with each node $v$ representing a protocol.
    #                 - $E$ consists of directed edges between nodes in $V$, with each edge $e(v_i, v_j)$ representing the flow of value from protocol $v_i$ to protocol $v_j$, derived from $\mathcal{C}_{sorted}$. The weight of each edge is proportional to the magnitude of the value change.

    #                 """

    # with tab3:
    #     st.write("# Network Diagram")
    #     st.write("This shows the global monthly token locked changes across all DeFi protocols")
    #     st.markdown("""
    #     **Color Legend for Nodes:**
    #     - ![#ffb71a](https://via.placeholder.com/15/ffb71a/000000?text=+) `Yellow`: Platform protocols (with complex lending and borrowing)
    #     - ![#ff4b4b](https://via.placeholder.com/15/ff4b4b/000000?text=+) `Red`: Token-only protocols
    #     """, unsafe_allow_html=True)
    #     year = st.selectbox("Select Year:", options=[2019, 2020, 2021, 2022, 2023], index=4)  # Example years, adjust as needed
    #     month = st.selectbox("Select Starting Month:", options=list(range(1, 13)), format_func=lambda x: f"{x:02d}", index=8)

    #     # Calculate the ending month and year
    #     if month == 12:
    #         end_month = 1
    #         end_year = year + 1
    #     else:
    #         end_month = month + 1
    #         end_year = year

    #     A = retrieve_table_A(bq)
    #     C = table_C_compare_months(bq, str(year), f"{month:02d}", str(end_year), f"{end_month:02d}")
    #     categorizer = NetworkVisualizer(C)
    #     result = categorizer.process(A)
    #     st.write(result.head(20))
    #     html_content = categorizer.plot_network(result)
    #     st.components.v1.html(html_content, height=600, scrolling=True)
    #     st.markdown(long_markdown, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
