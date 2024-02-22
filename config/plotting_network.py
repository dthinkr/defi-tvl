import pandas as pd
import re
import json
from pyvis.network import Network

class TokenCategorizer:
    def __init__(self, df):
        self.df = df.copy()
        with open('config/rev_map.json', 'r') as f:
            self.rev_map = json.load(f)
        self.manual_mapping = {'FRAX': '359',}

        self.categories = {'rev_map': None, 'LP': None, 'UNKNOWN': None, 'Other': None}
        self.eth_address_pattern = re.compile(r'0x[a-fA-F0-9]{40}')
        self.top_token_names = ['USDC', 'WETH', 'USDT', 'DAI', 'WBTC', 'BUSD', 'WBNB', 'ETH', 'BTCB',
                                'TUSD', 'RENBTC', 'DOT', 'HBTC', 'WMATIC', 'USDP', 'SUSD', 'MANA',
                                'ENJ', 'HUSD', 'FRAX']
        
    def categorize_tokens(self):
        self.categories['rev_map'] = self.df[self.df['token_name'].isin(self.rev_map.keys())]
        self.categories['LP'] = self.df[self.df['token_name'].str.contains('LP') & ~self.df['token_name'].isin(self.rev_map.keys())]
        self.categories['UNKNOWN'] = self.df[self.df['token_name'].str.contains('UNKNOWN') & ~self.df['token_name'].isin(self.rev_map.keys())]
        self.categories['Other'] = self.df[~self.df['token_name'].str.contains('LP|UNKNOWN') & ~self.df['token_name'].isin(self.rev_map.keys())]
        
    def process_unknown(self, A):
        # Check if the DataFrame is empty or if 'token_name' column is missing
        if self.categories['UNKNOWN'].empty or 'token_name' not in self.categories['UNKNOWN'].columns:
            print("DataFrame is empty or 'token_name' column is missing.")
            return  # Exit the function if the condition is met

        unique_token_names = self.categories['UNKNOWN']['token_name'].unique()
        unique_addresses_list = list({match for name in unique_token_names 
                                    for match in self.eth_address_pattern.findall(str(name))})
        
        address_to_id_mapping = {address: A.loc[A['address'].str.contains(address, na=False), 'id'].iloc[0] 
                                for address in unique_addresses_list
                                if A['address'].str.contains(address, na=False).any()}
        
        self.categories['UNKNOWN'] = self.categories['UNKNOWN'][self.categories['UNKNOWN']['token_name'].apply(lambda x: any(match in address_to_id_mapping for match in self.eth_address_pattern.findall(str(x))))]
        self.categories['UNKNOWN']['token_name'] = self.categories['UNKNOWN']['token_name'].apply(lambda x: next((address_to_id_mapping[match] for match in self.eth_address_pattern.findall(str(x)) if match in address_to_id_mapping), "Not Found"))
        
    def process_other(self):
        def apply_manual_mapping_or_filter(token_name):
            if token_name in self.manual_mapping:
                return self.manual_mapping[token_name]  
            elif token_name in self.top_token_names:
                return token_name 
            else:
                return None  
        
        self.categories['Other']['mapped_or_filtered'] = self.categories['Other']['token_name'].apply(apply_manual_mapping_or_filter)
        self.categories['Other'] = self.categories['Other'].dropna(subset=['mapped_or_filtered'])
        self.categories['Other']['token_name'] = self.categories['Other']['mapped_or_filtered']
        self.categories['Other'] = self.categories['Other'].drop(columns=['mapped_or_filtered'])
        
    def map_rev_map(self):
        self.categories['rev_map']['token_name'] = self.categories['rev_map']['token_name'].map(self.rev_map)
        
    def merge_categories(self):
        self.C_merged = pd.concat([self.categories['rev_map'], self.categories['UNKNOWN'], self.categories['Other']])

    def process_result_sorted(self, result, A):
        sort_column = 'value_usd_change' if 'value_usd_change' in result.columns else 'value_usd'

        result_sorted = result.sort_values(by=sort_column, ascending=False).head(3000)

        def is_not_integer_string(s):
            try:
                int(s)
                return False
            except ValueError:
                return True

        result_sorted['non_listed_protocols'] = result_sorted['token_name'].apply(is_not_integer_string)

        result_sorted['id'] = result_sorted['id'].astype(str)
        result_sorted['token_name'] = result_sorted['token_name'].astype(str)
        A['id'] = A['id'].astype(str)

        id_to_name = pd.Series(A['name'].values, index=A['id']).to_dict()
        id_to_url = pd.Series(A['url'].values, index=A['id']).to_dict()

        result_sorted['destination_node'] = result_sorted['id'].apply(lambda x: id_to_name.get(x, x))
        result_sorted['source_node'] = result_sorted['token_name'].apply(lambda x: id_to_name.get(x, x))
        result_sorted['url'] = result_sorted['id'].apply(lambda x: id_to_url.get(x, None))

        return result_sorted
        
    def process(self, A):
        self.categorize_tokens()
        self.process_unknown(A)
        self.process_other()
        self.map_rev_map()
        self.merge_categories()
        
        final_result = self.process_result_sorted(self.C_merged, A)
        return final_result
    

    def plot_network(self, result_sorted):
        # Initialize Pyvis network
        net = Network(notebook=True, height="750px", width="100%", bgcolor="#FFFFFF", font_color="black", directed=True, cdn_resources="in_line")

        # Track all unique nodes to avoid duplication
        unique_nodes = set()

        # Add nodes and edges
        for index, row in result_sorted.iterrows():
            source_node = row['source_node']
            destination_node = row['destination_node']
            url = row['url']
            non_listed_protocols = row['non_listed_protocols']
            value_usd_change = row['value_usd_change']  # Assuming this column exists in result_sorted
            
            # Determine node color based on non_listed_protocols
            node_color = "#ffb71a" if not non_listed_protocols else "#ff4b4b"
            
            # Reverse the edge direction if value_usd_change is negative
            if value_usd_change < 0:
                source_node, destination_node = destination_node, source_node
            
            # Add nodes if they haven't been added yet
            if source_node not in unique_nodes:
                net.add_node(source_node, label=source_node, title=f"<a href='{url}' target='_blank'>{source_node}</a>", color=node_color)
                unique_nodes.add(source_node)
            if destination_node not in unique_nodes:
                net.add_node(destination_node, label=destination_node, title=f"<a href='{url}' target='_blank'>{destination_node}</a>", color=node_color)
                unique_nodes.add(destination_node)
            
            # Add directed edge with value_usd as title for hover details
            edge_width = abs(row['value_usd_change']) / max(abs(result_sorted['value_usd_change'])) * 10  # Scale for visibility
            net.add_edge(source_node, destination_node, title=f"USD Change: ${row['value_usd_change']:.2f}", width=edge_width, arrows="to")

        net.set_options("""
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
            "gravitationalConstant": -25,
            "centralGravity": 0.005,
            "springLength": 150,
            "springConstant": 0.05,
            "damping": 4
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
        """)
        
        return net.generate_html()