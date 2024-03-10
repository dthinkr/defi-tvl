import os
import json
from datetime import datetime, timedelta
import sys
from collections import defaultdict

data_dir = "docs/data/network"
start_date = datetime(2024, 2, 4)
end_date = datetime(2024, 3, 4)

combined_data = {}

current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    file_path = os.path.join(data_dir, f"{date_str}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            combined_data[date_str] = data
    else:
        print(f"No data file for {date_str}.")
    
    current_date += timedelta(days=1)

formatted_data = {
    "directed": True,
    "multigraph": True,
    "graph": {},
    "nodes": [],
    "links": []
}

node_degrees = {}

for date, data in combined_data.items():
    for node in data['nodes']:
        if node['id'] not in node_degrees:
            node_degrees[node['id']] = {'degree': 0, 'modularity': 1}
        
        node_degrees[node['id']][f'degree_{date}'] = node_degrees[node['id']].get(f'degree_{date}', 0) + 1

    for link in data['links']:
        node_degrees[link['source']]['degree'] += 1
        node_degrees[link['target']]['degree'] += 1

        # Include size and date in the formatted_data['links']
        formatted_data['links'].append({
            "Date": date,
            "source": link['source'],
            "target": link['target'],
            "size": link['size'],  # Assuming 'size' exists in your original data
            "key": 0
        })

# Aggregate edges with the same source and target, including self-directed edges
aggregated_links = defaultdict(lambda: {"size": 0, "dates": []})
for link in formatted_data['links']:
    key = (link['source'], link['target'])
    aggregated_links[key]["size"] += link['size']
    if link['Date'] not in aggregated_links[key]["dates"]:
        aggregated_links[key]["dates"].append(link['Date'])

# Convert aggregated links back to the required format, choosing how to represent the date(s)
final_links = [{"source": source, "target": target, "size": size, "Date": dates[-1], "key": 0} 
               for (source, target), details in aggregated_links.items()
               for size, dates in [(details["size"], details["dates"])]]

# Apply the filtering for nodes based on the degree threshold
min_degree = 80
filtered_node_ids = {node_id for node_id, details in node_degrees.items() if details['degree'] >= min_degree}

# Ensure links only connect nodes that passed the filter
final_filtered_links = [link for link in final_links if link['source'] in filtered_node_ids and link['target'] in filtered_node_ids]

# Construct the list of filtered nodes to include in formatted_data
filtered_nodes = [{'id': node_id, **details} for node_id, details in node_degrees.items() if node_id in filtered_node_ids]

# Update formatted_data with filtered nodes and links
formatted_data['nodes'] = filtered_nodes
formatted_data['links'] = final_filtered_links

json.dump(formatted_data, sys.stdout)