import sys
import os

sys.path.append(os.getcwd())

import altair as alt

import pandas as pd

# import pandas_profiling
# from streamlit_pandas_profiling import st_profile_report

import streamlit as st
import streamlit.components.v1 as components

from config.config import CACHE_DIR

import networkx as nx
from pyvis.network import Network


@st.cache_data
def load_data():
    """Load datasets from cache and return as DataFrames."""
    tvl_by_type = pd.read_csv(CACHE_DIR + "db_tvl_long.csv")
    category_df = pd.read_csv(CACHE_DIR + "db_category.csv")
    chain_dc_true = pd.read_csv(CACHE_DIR + "chain-dataset-All-doublecounted=true.csv")
    nodes_df = pd.read_csv(CACHE_DIR + "nodes_df.csv")
    edges_df = pd.read_csv(CACHE_DIR + "edges_df.csv")
    return tvl_by_type, category_df, chain_dc_true, nodes_df, edges_df


def prepare_tvl_by_type(tvl_by_type):
    """Calculate the rolling mean for TVL by type data."""
    tvl_by_type["totalLiquidityUSD"] = (
        tvl_by_type.groupby("type")["totalLiquidityUSD"]
        .transform(lambda x: x.rolling(window=14).mean())
        .fillna(0)
    )
    return tvl_by_type


def create_stacked_area_chart(data, normalize=False):
    """Visualize stacked area charts."""
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
    """Visualize project distribution across chains."""
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
    """A pie chart for entity distribution by type."""
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


@st.cache_data
def create_network_chart(nodes_df, edges_df, percentage=100, selected_nodes=None):
    """An interactive network chart using pyvis."""
    num_nodes = int(len(nodes_df) * percentage / 100)
    top_nodes = nodes_df.nlargest(num_nodes, "size")
    filtered_edges = edges_df[
        edges_df["source"].isin(top_nodes["name"])
        & edges_df["target"].isin(top_nodes["name"])
    ]

    G = nx.from_pandas_edgelist(
        filtered_edges, "source", "target", ["weight"], create_using=nx.DiGraph()
    )
    node_sizes = nodes_df.set_index("name")["size"].to_dict()
    for node in G.nodes():
        G.nodes[node]["size"] = node_sizes.get(node, min(node_sizes.values()))

    nt = Network(notebook=True, directed=True)
    nt.from_nx(G)
    for node in nt.nodes:
        node["value"] = G.nodes[node["label"]]["size"]

    if selected_nodes:
        for node in nt.nodes:
            if node["label"] in selected_nodes:
                node["color"] = "#FF0000"

    try:
        path = "/tmp"
        nt.save_graph(f"{path}/pyvis_graph.html")
        HtmlFile = open(f"{path}/pyvis_graph.html", "r", encoding="utf-8")
    except:
        path = "/html_files"
        nt.save_graph(f"{path}/pyvis_graph.html")
        HtmlFile = open(f"{path}/pyvis_graph.html", "r", encoding="utf-8")

    components.html(HtmlFile.read(), height=435)


def main():
    """Execute the Streamlit app."""
    st.write("# DeFi TVL")

    tvl_by_type, category_df, chain_dc_true, nodes_df, edges_df = load_data()
    tvl_by_type = prepare_tvl_by_type(tvl_by_type)

    st.write("### TVL")
    st.markdown(
        "Source: API -> Processed Data, Double Counted<sup><a href='#footnote1'>1</a></sup>",
        unsafe_allow_html=True,
    )
    st.altair_chart(
        create_stacked_area_chart(tvl_by_type, normalize=True), use_container_width=True
    )
    st.altair_chart(create_stacked_area_chart(tvl_by_type), use_container_width=True)

    st.write("### Types")
    st.altair_chart(create_pie_chart(category_df), use_container_width=True)

    st.write("### Chains")
    st.altair_chart(create_chain_chart(category_df), use_container_width=True)

    st.write("### Network Plot of Protocols and Tokens")
    percentage = st.slider(
        "Percentage of Nodes Displayed", min_value=10, max_value=100, value=100
    )

    node_names = nodes_df["name"].unique().tolist()
    node_names.sort()

    selected_nodes = st.multiselect("Select node(s) to highlight", node_names)
    create_network_chart(nodes_df, edges_df, percentage, selected_nodes)

    # st_profile_report(category_df.profile_report())

    st.markdown(
        "<sup id='footnote1'>1</sup> Excluding double counting is possible on chain-level, but it is not possible on protocol-level.",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
