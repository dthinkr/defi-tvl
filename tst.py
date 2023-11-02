import os
import networkx as nx
from pyvis.network import Network
from google.cloud import bigquery
from config.config import TABLES
from src.query import BigQueryClient
from matplotlib import pyplot as plt


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "private-key.json"

def create_erd(bq_client, tables_dict):
    G = nx.Graph()

    for key, table_name in tables_dict.items():
        schema = bq_client.get_table_schema(table_name)
        for field in schema:
            G.add_node(field.name, table=table_name)
            
            # Checking for potential foreign keys
            if 'id' in field.name and field.name != f"{table_name}_id":
                potential_ref_table = field.name.replace('_id', '')
                
                # Check if the potential referenced table is in our tables_dict
                if potential_ref_table in tables_dict.values():
                    G.add_edge(table_name, potential_ref_table, field=field.name)

    # Visualize the graph using pyvis
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 12))
    nx.draw_networkx(G, pos)
    plt.show()

bq = BigQueryClient()
create_erd(bq, TABLES)