import altair as alt
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    long_df = pd.read_csv("data/tvl/cache/db_tvl_long.csv")
    category_df = pd.read_csv("data/tvl/cache/db_category.csv")
    original_data = pd.read_csv(
        "data/tvl/cache/chain-dataset-All-doublecounted=true.csv"
    )
    return long_df, category_df, original_data


# @st.cache_data
# def prepare_original_data(original_data, category_df):
#     melted_data = original_data.melt(id_vars=["Protocol"], var_name="date", value_name="totalLiquidityUSD")
#     merged_data = melted_data.merge(category_df[['name', 'type']], left_on='Protocol', right_on='name', how='left')
#     merged_data = merged_data[~merged_data['type'].isnull()]
#     aggregated_data = merged_data.groupby(['type', 'date'])['totalLiquidityUSD'].sum().reset_index()
#     aggregated_data['totalLiquidityUSD'] = aggregated_data['totalLiquidityUSD'] / 1e9
#     return aggregated_data


def prepare_long_df(long_df):
    long_df["totalLiquidityUSD"] = (
        long_df.groupby("type")["totalLiquidityUSD"]
        .transform(lambda x: x.rolling(window=14).mean())
        .fillna(0)
    )
    return long_df


def create_stacked_area_chart(data, normalize=False):
    selection = alt.selection_point(fields=["type"], bind="legend")
    interval = alt.selection_interval()

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
            color=alt.Color("type:N", title="Type", legend=alt.Legend(title="Type")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
            tooltip=["date", "type", "totalLiquidityUSD"],
        )
        .properties(title=title)
        .add_params(selection, interval)  # Updated from add_selection to add_params
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

    long_df, category_df, original_data = load_data()
    long_df = prepare_long_df(long_df)

    st.write("### TVL")
    st.markdown("Source: API -> Processed Data, Double Counted<sup><a href='#footnote1'>1</a></sup>", unsafe_allow_html=True)
    st.altair_chart(
        create_stacked_area_chart(long_df, normalize=True), use_container_width=True
    )
    st.altair_chart(create_stacked_area_chart(long_df), use_container_width=True)

    # original_data = prepare_original_data(original_data, category_df)
    # st.altair_chart(create_stacked_area_chart(original_data), use_container_width=True)

    st.write("### Types")
    st.altair_chart(create_pie_chart(category_df), use_container_width=True)

    st.write("### Chains")
    st.altair_chart(create_chain_chart(category_df), use_container_width=True)

    st.markdown("<sup id='footnote1'>1</sup> Excluding double counting is possible on chain-level, but it is not possible on protocol-level.", unsafe_allow_html=True)


main()
