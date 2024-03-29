from config.config import TABLES, PRIMARY_TOKEN_TO_PROTOCOL, CATEGORY_MAPPING, MAPPING_PATH, SIMILARIY_THRESHOLD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import pandas as pd
import json
import numpy as np
import os
import dask.dataframe as dd
import os

try:
    NUM_CORES = max(1, int(os.cpu_count() * 0.8))
except:
    NUM_CORES = 1

class ETLNetwork:
    def __init__(self, bq):
        self.bq = bq
        self.mapping_path = MAPPING_PATH
        self.rev_map, self.categories, self.id_to_info = {}, {}, {}
        required_files = ['rev_map.json', 'token_to_protocol.json', 'id_to_info.json']
        missing_files = [file for file in required_files if not os.path.exists(self.mapping_path + file)]
        if missing_files:
            print(f"Missing files: {missing_files}")
            self.update_mapping()
        self._load_mappings()

    def _retrieve_update_date(self, tables = [TABLES['A'], TABLES['C']]):
        for table in tables:
            self.bq._get_last_modified_time(table)
        raise NotImplementedError
    
    def _load_mappings(self):
        self.rev_map = self._load_json('rev_map.json')
        self.categories = self._load_json('token_to_protocol.json')
        self.id_to_info = self._load_json('id_to_info.json')

    def _load_json(self, filename):
        with open(os.path.join(self.mapping_path, filename), 'r') as file:
            return json.load(file)

    def _default_handler(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
    def _save_json(self, data, filename):
        path = os.path.join(self.mapping_path, filename)
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4, default=self._default_handler)

    def _similarity_scores(self, categories, A):
        """
        Calculates similarity scores between tokens and protocols to map each token to the most similar protocol.
        
        This method uses TF-IDF vectorization and cosine similarity to compare the textual representation of tokens
        against a set of protocols. Each token is then mapped to the protocol with the highest similarity score,
        provided the score exceeds a predefined threshold.

        Parameters:
        - categories (dict): A dictionary containing token categories with their respective tokens and metadata.
        - A (pd.DataFrame): A DataFrame containing protocol information, including textual descriptions.

        Returns:
        - dict: A mapping of token names to their most similar protocol, including the protocol's ID and name.
        """
        input_tokens = {}
        for category_name, tokens in categories.items():
            for token, data in tokens.items():
                if isinstance(data['id'], str):
                    input_tokens[token] = data

        token_names = list(input_tokens.keys())
        combined_texts = token_names + A['all_text'].tolist()
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(combined_texts)
        tfidf_tokens = tfidf_matrix[:len(token_names)]
        tfidf_A_texts = tfidf_matrix[len(token_names):]
        similarity_scores = cosine_similarity(tfidf_tokens, tfidf_A_texts)

        best_matches_indices = similarity_scores.argmax(axis=1)
        best_scores = similarity_scores.max(axis=1)
        threshold = SIMILARIY_THRESHOLD
        token_to_protocol = {}

        for i, token_name in enumerate(token_names):
            if best_scores[i] >= threshold:
                best_match_index = best_matches_indices[i]
                matched_id = A.iloc[best_match_index]['id']
                matched_name = A.iloc[best_match_index]['name']
                token_to_protocol[token_name] = {'id': matched_id, 'name': matched_name}

        return token_to_protocol
    
    def update_mapping(self):
        """
        Updates the internal mappings of tokens to protocols based on the latest data from BigQuery.

        This method fetches the latest data from BigQuery, processes it to update the reverse mapping (rev_map),
        token to protocol mapping (categories), and the ID to information mapping (id_to_info). It handles the
        extraction, transformation, and loading (ETL) of token and protocol data to ensure the mappings reflect
        the current state of the blockchain data. The updated mappings are then saved to local JSON files.

        The process involves:
        - Fetching the latest protocol and token data from BigQuery.
        - Calculating total TVLs for protocols and sorting them.
        - Updating the reverse mapping for tokens to their respective protocol IDs.
        - Classifying tokens into categories and updating the token to protocol mappings based on similarity scores and predefined rules.
        - Saving the updated mappings to local JSON files for use in data processing and analysis.
        """
        print("Updating mapping...")
        A = self.bq.get_dataframe(TABLES['A'])
        tvl_column = 'currentChainTvls' if 'currentChainTvls' in A.columns else 'chainTvls'
        A['totalTvls'] = A[tvl_column].apply(lambda x: sum(ast.literal_eval(x).values()) if isinstance(x, str) and x.strip() != '' else 0)
        A = A.sort_values(by='totalTvls', ascending=False)

        # Update Rev Map
        rev_map = {}
        for idx, row in A.iterrows():
            if pd.notna(row['assetToken']) and row['assetToken'] != "-":
                rev_map[row['assetToken']] = row['id']
            if pd.notna(row['symbol']) and row['symbol'] != "-":
                rev_map[row['symbol']] = row['id']
        
        self._save_json(rev_map, 'rev_map.json')
        
        unique_token_names = self.bq.get_unique_token_names(TABLES['C']).dropna()
        frequency_df = self.bq.get_token_frequency(TABLES['C'])
        frequency_dict = frequency_df.set_index('token_name')['frequency'].to_dict()
        categories = {'MAP': {}, 'LP': {}, 'UNKNOWN': {}, 'PRIMARY': {}, 'OTHER': {}}
        for idx, row in unique_token_names.iterrows():
            token_name = row['token_name']
            category = ''
            if token_name in rev_map:
                category = 'MAP'
            elif "LP" in token_name:
                category = 'LP'
            elif "UNKNOWN" in token_name:
                category = 'UNKNOWN'
            elif "-" in token_name:
                category = 'OTHER'
            else:
                category = 'PRIMARY'
            categories[category][token_name] = {
                'id': rev_map.get(token_name, None),
                'frequency': frequency_dict.get(token_name, 0)  # Default to 0 if not found
            }

        """
            - update the PRIMARY category and mark the rest as either MAP, LP, UNKNOWN, or OTHER
            - this is done using a manually defined mapping in config.config
        """
        sorted_primary = sorted(categories['PRIMARY'].items(), key=lambda x: x[1]['frequency'], reverse=True)
        categories['PRIMARY'] = {token: data for token, data in sorted_primary}

        for token, protocol_name in PRIMARY_TOKEN_TO_PROTOCOL.items():
            matching_row = A[A['name'] == protocol_name]
            if not matching_row.empty:
                matching_id = matching_row.iloc[0]['id']
                if token in categories['PRIMARY']:
                    categories['PRIMARY'][token]['id'] = matching_id

        for category_name, tokens in categories.items():
            for token, data in tokens.items():
                if data['id'] is None:
                    if category_name == 'PRIMARY':
                        categories[category_name][token]['id'] = token  
                    else:
                        categories[category_name][token]['id'] = category_name
        """ 
            - further update using similarity scores
            - read ummapped tokens
            - find the most similar token in the mapping
            - if the similarity score is high, we can use the mapping
            - update and overwrite the old mapping
        """
        A['all_text'] = A.apply(lambda x: ' '.join(x.fillna('').replace('None', '').astype(str)), axis=1)
        mapped_tokens = self._similarity_scores(categories, A)

        for token_name, mapping_info in mapped_tokens.items():
            for category_name, tokens in categories.items():
                if token_name in tokens:
                    categories[category_name][token_name]['id'] = mapping_info['id']
                    break
        
        self._save_json(categories, 'token_to_protocol.json')

        # Update ID to Info
        detailed_to_broad = {det: broad for broad, dets in CATEGORY_MAPPING.items() for det in dets}
        id_to_info = {row['id']: {'name': row['name'], 'category': detailed_to_broad.get(row['category'], 'Unknown')} for index, row in A.iterrows()}

        self._save_json(id_to_info, 'id_to_info.json')

    def _process_edges(self, links):
        edge_aggregate = {}
        for link in links:
            key = tuple(sorted([link['source'], link['target']]))
            edge_aggregate[key] = edge_aggregate.get(key, 0) + (link['size'] if link['source'] < link['target'] else -link['size'])

        final_links = [{'source': node1 if net_size > 0 else node2, 'target': node2 if net_size > 0 else node1, 'size': abs(net_size)} for (node1, node2), net_size in edge_aggregate.items() if net_size != 0]

        return final_links

    def process_dataframe(self, C: pd.DataFrame, TOP_X: int = None, mode: str = 'usd', type: bool = False):

        if TOP_X != None:
            raise NotImplementedError("TOP_X is not implemented yet")

        # Initialize the new columns with NaNs or zeros
        C['qty_from'] = C['qty_to'] = C['usd_from'] = C['usd_to'] = None

        # For rows where 'usd_change' is negative, it means the flow is from 'from_node' to 'to_node'
        C.loc[C['usd_change'] < 0, ['qty_from', 'usd_from']] = C.loc[C['usd_change'] < 0, ['qty', 'usd']].values

        # For rows where 'usd_change' is positive, it means the flow is from 'to_node' to 'from_node'
        C.loc[C['usd_change'] >= 0, ['qty_to', 'usd_to']] = C.loc[C['usd_change'] >= 0, ['qty', 'usd']].values

        # Function to find the token_id from self.categories
        def find_token_id(token_name):
            for category, tokens in self.categories.items():
                if token_name in tokens:
                    return str(tokens[token_name].get('id', None))
            return None

        # Apply the function to find token_id for each row in DataFrame 'C'
        C['token_id'] = C['token_name'].apply(find_token_id)

        # Ensure 'id' is also converted to string to avoid type mismatch
        C['id'] = C['id'].astype(str)

        # Vectorized operation to set from_node and to_node based on usd_change
        C['from_node'] = C['id'].where(C['usd_change'] < 0, C['token_id'])
        C['to_node'] = C['token_id'].where(C['usd_change'] < 0, C['id'])

        # Select only the required columns and adjust 'qty_change' and 'usd_change' to be absolute values
        C = C[['from_node', 'to_node', 'chain_name', 'qty_from', 'qty_to', 'usd_from', 'usd_to', 'qty_change', 'usd_change']].copy()
        C['qty_change'] = C['qty_change'].abs()
        C['usd_change'] = C['usd_change'].abs()

        def replace_with_name(value):
            return self.id_to_info.get(str(value), {}).get('name', value)

        C['from_node'] = C['from_node'].apply(replace_with_name)
        C['to_node'] = C['to_node'].apply(replace_with_name)


        def get_category(node_name):
            for id, info in self.id_to_info.items():
                if info.get('name') == node_name:
                    return info.get('category', 'AGGREGATED')  # Default to 'AGGREGATED' if category is not found
            # Check if node_name is not what we expect (e.g., numeric or specific unwanted IDs)
            if node_name.isdigit() or node_name == '3594':  # You can add more conditions here
                return 'AGGREGATED'
            return node_name  # Return node_name if it doesn't match any special conditions
        

        if type:

            C = dd.from_pandas(C, npartitions=NUM_CORES)

            C['from_node_category'] = C['from_node'].apply(get_category, meta=('from_node', 'object'))
            C['to_node_category'] = C['to_node'].apply(get_category, meta=('to_node', 'object'))

            C = C.compute()
            C = C.replace({pd.NA: None})

            # Convert columns to numeric, ensuring `None` values are handled
            C['qty_from'] = pd.to_numeric(C['qty_from'], errors='coerce').fillna(0)
            C['qty_to'] = pd.to_numeric(C['qty_to'], errors='coerce').fillna(0)
            C['usd_from'] = pd.to_numeric(C['usd_from'], errors='coerce').fillna(0)
            C['usd_to'] = pd.to_numeric(C['usd_to'], errors='coerce').fillna(0)

            # C['from_node_category'] = C['from_node'].apply(get_category)
            # C['to_node_category'] = C['to_node'].apply(get_category)

            # Initialize a dictionary to hold the total values for each category, starting with 0
            category_values = {category: 0 for category in set(C['from_node_category']).union(set(C['to_node_category']))}
            
            # Choose the mode: 'usd' or 'qty'
            value_column_from = 'usd_from' if mode == 'usd' else 'qty_from'
            value_column_to = 'usd_to' if mode == 'usd' else 'qty_to'

            # Aggregate 'from_value' and 'to_value' for each category
            from_aggregation = C.groupby('from_node_category')[value_column_from].sum().fillna(0)
            to_aggregation = C.groupby('to_node_category')[value_column_to].sum().fillna(0)

            # Combine the aggregations
            category_values_aggregate = from_aggregation.add(to_aggregation, fill_value=0)


            # Ensure all categories are included, even those without transactions
            all_categories = set(C['from_node_category']).union(set(C['to_node_category']))
            category_values = {category: 0 for category in all_categories}  # Initialize all to 0

            # Update the dictionary with aggregated values
            for category in category_values_aggregate.index:
                category_values[category] += category_values_aggregate[category]


            # Generate nodes with their sizes based on the aggregated values
            nodes = [{'id': category, 'size': size, 'category': category} for category, size in category_values.items()]

            # Generate links as before
            links = []
            for (from_cat, to_cat), group in C.groupby(['from_node_category', 'to_node_category']):
                size = group['usd_change'].sum() if mode == 'usd' else group['qty_change'].sum()
                links.append({'source': from_cat, 'target': to_cat, 'size': size, 'chain': 'aggregated'})

            # Handling self-links for within-category transfers
            for category in category_values.keys():
                within_category_size = C[(C['from_node_category'] == category) & (C['to_node_category'] == category)]['usd_change'].sum() if mode == 'usd' else C[(C['from_node_category'] == category) & (C['to_node_category'] == category)]['qty_change'].sum()
                if within_category_size != 0:
                    links.append({'source': category, 'target': category, 'size': within_category_size, 'chain': 'aggregated'})


        network_json = {
            'nodes': nodes,
            'links': links
        }

        network_json['links'] = self._process_edges(network_json['links'])

        return network_json
