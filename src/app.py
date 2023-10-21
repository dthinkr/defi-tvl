import altair as alt
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    long_df = pd.read_csv("data/tvl/cache/df_long.csv")
    category_df = pd.read_csv("data/tvl/cache/category.csv")
    return long_df, category_df


def prepare_long_df(long_df):
    long_df["totalLiquidityUSD"] = (
        long_df.groupby("type")["totalLiquidityUSD"]
        .transform(lambda x: x.rolling(window=14).mean())
        .fillna(0)
    )
    return long_df


def create_stacked_area_chart(data, normalize=False):
    y_encoding = alt.Y(
        "totalLiquidityUSD:Q",
        stack=True,
        axis=alt.Axis(format=".0f", title="Total Liquidity (in billions)"),
    )
    if normalize:
        y_encoding.stack = "normalize"
        title = "Normalized Stacked Area Chart"
    else:
        title = "Stacked Area Chart"

    chart = (
        alt.Chart(data)
        .mark_area()
        .encode(
            x="date:T",
            y=y_encoding,
            color=alt.Color("type:N", title="Type"),
            tooltip=["date", "type", "totalLiquidityUSD"],
        )
        .properties(title=title)
    )
    return chart


def create_chain_chart(category_df):
    chain_counts = category_df["chain"].value_counts()
    filtered_chain_counts = chain_counts[chain_counts >= 30]
    chain_df = filtered_chain_counts.reset_index()
    chain_df.columns = ["Chain", "ProjectCount"]

    chart = (
        alt.Chart(chain_df)
        .mark_bar()
        .encode(
            x=alt.X("Chain:O", title="Chain", sort="-y"),
            y=alt.Y("ProjectCount:Q", title="Number of Projects"),
            tooltip=["Chain", "ProjectCount"],
        )
        .properties(
            title="Distribution of Projects Across Different Chains",
            width=600,
            height=400,
        )
    )
    return chart


def create_pie_chart(category_df):
    type_counts = category_df["type"].value_counts().reset_index()
    type_counts.columns = ["Type", "Count"]
    chart = (
        alt.Chart(type_counts)
        .mark_arc(innerRadius=0)
        .encode(
            theta="Count:Q",
            color=alt.Color("Type:N", title="Type"),
            tooltip=["Type", "Count"],
        )
        .properties(title="Distribution of Entities by Type", width=400, height=400)
    )
    return chart


def main():
    st.write("# DeFi TVL")

    long_df, category_df = load_data()
    long_df = prepare_long_df(long_df)

    st.write("### TVL")
    st.altair_chart(
        create_stacked_area_chart(long_df, normalize=True), use_container_width=True
    )
    st.altair_chart(create_stacked_area_chart(long_df), use_container_width=True)

    st.write("### Types")
    st.altair_chart(create_pie_chart(category_df), use_container_width=True)

    st.write("### Chains")
    st.altair_chart(create_chain_chart(category_df), use_container_width=True)


main()
