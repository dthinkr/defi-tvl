import streamlit as st
import altair as alt
import pandas as pd

long_df = pd.read_csv('data/tvl/cache/df_long.csv')

long_df['totalLiquidityUSD'] = long_df.groupby('type')['totalLiquidityUSD'].transform(lambda x: x.rolling(window=14).mean()).fillna(0)

st.write("# DeFi TVL")

st.write("### Normalized Stacked Area Chart")
chart_normalized = alt.Chart(long_df).mark_area().encode(
    x="date:T",
    y=alt.Y("totalLiquidityUSD:Q", stack="normalize", axis=alt.Axis(format='.0f', title='Total Liquidity (in billions)')),
    color="type:N",
    tooltip=['date', 'type', 'totalLiquidityUSD']
)
st.altair_chart(chart_normalized, use_container_width=True)

st.write("### Non-Normalized Stacked Area Chart")
chart_non_normalized = alt.Chart(long_df).mark_area().encode(
    x="date:T",
    y=alt.Y("totalLiquidityUSD:Q", stack=True, axis=alt.Axis(format='.0f', title='Total Liquidity (in billions)')),
    color="type:N",
    tooltip=['date', 'type', 'totalLiquidityUSD']
)
st.altair_chart(chart_non_normalized, use_container_width=True)

category_df = pd.read_csv('data/tvl/cache/category.csv')
chain_counts = category_df['chain'].value_counts()
filtered_chain_counts = chain_counts[chain_counts >= 10]

# Reset index and rename columns for clarity
chain_df = filtered_chain_counts.reset_index()
chain_df.columns = ['Chain', 'ProjectCount']

chain_chart = alt.Chart(chain_df).mark_bar().encode(
    x=alt.X('Chain:O', title='Chain', sort='-y'),
    y=alt.Y('ProjectCount:Q', title='Number of Projects'),
    tooltip=['Chain', 'ProjectCount']
).properties(
    title='Distribution of Projects Across Different Chains',
    width=600,
    height=400
)

st.write("### Distribution of Projects Across Different Chains")
st.altair_chart(chain_chart, use_container_width=True)

percentage_distribution = (filtered_chain_counts / filtered_chain_counts.sum()) * 100
percentage_chart = alt.Chart(pd.DataFrame(percentage_distribution.reset_index())).mark_bar().encode(
    x=alt.X('index:O', title='Chain', sort='-y'),
    y=alt.Y('0:Q', title='Percentage of Projects (%)'),
    tooltip=['index', '0']
).properties(
    title='Percentage Distribution of Projects Across Different Chains',
    width=600,
    height=400
)

st.write("### Percentage Distribution of Projects Across Different Chains")
st.altair_chart(percentage_chart, use_container_width=True)
