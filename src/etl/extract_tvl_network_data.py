import pandas as pd
import duckdb
import random
import altair as alt
import networkx as nx

# 1. Load the Parquet file
con = duckdb.connect(database=":memory:")
con.execute(
    "CREATE TABLE crypto_data AS SELECT * FROM parquet_scan('../data/tvl/db/crypto_merged.parquet')"
)

# 2. Fetch data into a DataFrame
df_crypto = con.execute("SELECT * FROM crypto_data").fetchdf()

# 3. Restructure the tokens data
all_token_dataframes = []
for index, row in df_crypto.iterrows():
    tokens_str = row["tokens"]
    if tokens_str and "NULL" not in tokens_str:
        tokens_data = eval(tokens_str.replace("NULL", "None"))
        df_tokens_temp = pd.DataFrame(tokens_data)
        if "tokens" in df_tokens_temp.columns:
            df_expanded_temp = df_tokens_temp["tokens"].apply(pd.Series)
            df_tokens_temp = pd.concat(
                [df_tokens_temp["date"], df_expanded_temp], axis=1
            )
        all_token_dataframes.append(df_tokens_temp)
df_tokens_final = pd.concat(all_token_dataframes)

# 4. Create a mapping between token symbols and protocols
known_mapping = {"ETH": "Ethereum", "LINK": "Chainlink", "USDT": "Tether"}
protocols = df_crypto["name"].unique().tolist()
tokens_to_map = [
    token
    for token in df_tokens_final.columns.drop("date")
    if token not in known_mapping.keys()
]
random_mapping = {token: random.choice(protocols) for token in tokens_to_map}
token_to_protocol_mapping = {**known_mapping, **random_mapping}

# 5. Construct the network graph
G = nx.DiGraph()
for protocol in protocols:
    node_size = random.randint(10, 500)
    G.add_node(protocol, size=node_size)
for token, protocol in token_to_protocol_mapping.items():
    target_protocol = random.choice([p for p in protocols if p != protocol])
    edge_width = random.randint(1, 10)
    G.add_edge(protocol, target_protocol, weight=edge_width)

# Ensure all nodes have a 'size' attribute
for node, data in G.nodes(data=True):
    if "size" not in data:
        G.nodes[node]["size"] = random.randint(10, 500)

# 6. Convert NetworkX data to DataFrames for Altair visualization
nodes_df = pd.DataFrame({"name": list(G.nodes())})
pos = nx.spring_layout(G)
nodes_df["x"], nodes_df["y"] = zip(*pos.values())
nodes_df["size"] = [data["size"] for _, data in G.nodes(data=True)]
edges_df = pd.DataFrame(
    list(G.edges(data=True)), columns=["source", "target", "weight"]
)
edges_df["weight"] = edges_df["weight"].map(lambda x: x["weight"])
node_lookup = nodes_df.set_index("name").to_dict(orient="index")
edges_df["source_x"] = edges_df["source"].map(lambda x: node_lookup[x]["x"])
edges_df["source_y"] = edges_df["source"].map(lambda x: node_lookup[x]["y"])
edges_df["target_x"] = edges_df["target"].map(lambda x: node_lookup[x]["x"])
edges_df["target_y"] = edges_df["target"].map(lambda x: node_lookup[x]["y"])

# Define paths for saving the dataframes in CSV format
nodes_csv_path = "../data/tvl/cache/nodes_df.csv"
edges_csv_path = "../data/tvl/cache/edges_df.csv"

# Save the dataframes as CSV files
nodes_df.to_csv(nodes_csv_path, index=False)
edges_df.to_csv(edges_csv_path, index=False)

nodes_csv_path, edges_csv_path
