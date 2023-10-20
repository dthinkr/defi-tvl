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