from pyvis.network import Network
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import matplotx
import pandas as pd

def save_heatmap(pivot_df: pd.DataFrame):
    # Generate heatmap
    with plt.style.context(matplotx.styles.duftify(matplotx.styles.dracula)):
        plt.figure(figsize=(12, 8))
        ax = sns.heatmap(pivot_df, cbar=False)
        plt.title('Protocol Activity Over Time')
        plt.xlabel('Date')
        plt.ylabel('Protocol Rank')
        pivot_df.columns = pd.DatetimeIndex(pivot_df.columns)
        unique_years = pivot_df.columns.year.drop_duplicates()
        first_dates_per_year = [pivot_df.columns[pivot_df.columns.year == year][0] for year in unique_years]
        ax.set_xticks([pivot_df.columns.get_loc(date) for date in first_dates_per_year])
        ax.set_xticklabels([date.strftime('%Y') for date in first_dates_per_year])
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig('data/protocol_activity_heatmap.png')  # Adjust path as needed
        plt.close()

class NetworkVisualizer:
    def __init__(self, notebook=True, height="750px", width="100%", bgcolor="#FFFFFF", font_color="black", directed=True, cdn_resources="in_line"):
        self.plot_settings = """
        {
        "nodes": {
            "font": {
            "size": 24
            }
        },
        "edges": {
            "color": {
            "inherit": true
            },
            "smooth": false
        },
        "physics": {
            "forceAtlas2Based": {
            "gravitationalConstant": -50,
            "centralGravity": 0.005,
            "springLength": 150,
            "springConstant": 0.05,
            "damping": 6
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
            "enabled": true,
            "iterations": 1000,
            "updateInterval": 25,
            "onlyDynamicEdges": true,
            "fit": true
            }
        }
        }
        """
        self.net = Network(notebook=notebook, height=height, width=width, bgcolor=bgcolor, font_color=font_color, directed=directed, cdn_resources=cdn_resources)


    def normalize_size(self, size, all_sizes, min_visual=5, max_visual=150):
        min_size, max_size = min(all_sizes), max(all_sizes)
        normalized = (size - min_size) / (max_size - min_size) if max_size > min_size else 1
        return normalized * (max_visual - min_visual) + min_visual

    def visualize_network(self, network_json, category_colors=None):
        # Default color for nodes if category_colors is not provided or a category is missing
        default_color = "#999999"  # Example gray color, adjust as needed

        all_sizes = [node['size'] for node in network_json['nodes']]
        for node in network_json['nodes']:
            # Determine the color for the node
            node_color = category_colors.get(node['category'], default_color) if category_colors else default_color
            self.net.add_node(node['id'], label=node['id'], size=self.normalize_size(node['size'], all_sizes), color=node_color)

        edge_data = defaultdict(lambda: {'size': 0, 'chains': defaultdict(int)})
        for link in network_json['links']:
            key = (link['source'], link['target'])
            edge_data[key]['size'] += link['size']
            edge_data[key]['chains'][link.get('chain', 'Unknown')] += link['size']

        all_edge_sizes = [data['size'] for data in edge_data.values()]
        for (source, target), data in edge_data.items():
            title = "\n".join([f"{chain}: {size}" for chain, size in data['chains'].items()])
            self.net.add_edge(source, target, title=title, value=self.normalize_size(data['size'], all_edge_sizes, 1, 10))

        self.net.set_options(self.plot_settings)
        return self.net.generate_html()