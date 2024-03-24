import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import scienceplots
plt.style.use('science')
import pandas as pd
import requests
import matplotlib.dates as mdates
from datetime import datetime, timedelta

import os
print(os.environ["PATH"])
os.environ["PATH"] += os.pathsep + '/usr/local/bin/'
os.environ["PATH"] += os.pathsep + '/Library/TeX/texbin/'

network_translation = {
    'erdos_renyi': 'Random',
    'watts_strogatz': 'Small-World',
    'barabasi_albert': 'Scale-Free',
    'complete': 'Fully Connected',
    'star': 'Star'
}

def generate_network_with_authority(network_type, n, clusters=0, authority_per_cluster=1):
    # Generate the base network
    G = None
    if network_type == 'erdos_renyi':
        G = nx.erdos_renyi_graph(n, 0.1)
    elif network_type == 'watts_strogatz':
        G = nx.watts_strogatz_graph(n, 4, 0.1)
    elif network_type == 'barabasi_albert':
        G = nx.barabasi_albert_graph(n, 2)
    elif network_type == 'complete':
        G = nx.complete_graph(n)
    elif network_type == 'star':
        G = nx.star_graph(n-1)
    else:
        raise ValueError("Unknown network type")
    
    # Skip clustering logic if clusters <= 1
    if clusters >= 1:
        nodes_per_cluster = n // clusters
        for cluster_index in range(clusters):
            start_node = cluster_index * nodes_per_cluster
            end_node = start_node + nodes_per_cluster
            cluster_nodes = list(range(start_node, end_node))
            
            # Add authority nodes to the cluster
            for _ in range(authority_per_cluster):
                authority_node = max(G.nodes) + 1
                edges_to_add = [(authority_node, node) for node in cluster_nodes]
                G.add_edges_from(edges_to_add)
                G.nodes[authority_node]['authority'] = True  # Tag the node as an authority node
    
    return G

def simulate_SI_model_with_authority(G, initial_infected):
    infected = set(initial_infected)
    propagation_steps = [infected.copy()]
    recovered = set()
    total_messages_sent = 0  # Initialize the counter for messages sent
    
    while len(infected) < len(G.nodes()):
        new_infected = set()
        for node in infected:
            if node in recovered:
                continue  # Skip recovered nodes
            for neighbor in G.neighbors(node):
                total_messages_sent += 1  # Increment for each neighbor checked
                if neighbor not in infected and neighbor not in recovered:
                    new_infected.add(neighbor)
                    if "authority" in G.nodes[neighbor]:  # Check if neighbor is an authority node
                        recovered.add(neighbor)  # Recover authority nodes immediately
                        for n in G.neighbors(neighbor):  # Infect all neighbors of the authority node
                            total_messages_sent += 1  # Increment for each neighbor of the authority node checked
                            if n not in infected:
                                new_infected.add(n)
        infected.update(new_infected)
        propagation_steps.append(infected.copy())
    
    return propagation_steps, total_messages_sent  # Return both propagation steps and total messages sent

def plot_all_steps_single_page(network_types, node_size, steps, clusters=0):
    # Calculate grid size
    rows = len(network_types)
    cols = steps
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))  # Adjust subplot size here
    
    for i, network_type in enumerate(network_types):
        G = generate_network_with_authority(network_type, node_size, clusters=clusters)
        initial_infected = [list(G.nodes())[0]]
        propagation_steps, _ = simulate_SI_model_with_authority(G, initial_infected)
        
        for step_number in range(steps):
            ax = axs[i, step_number] if rows > 1 else axs[step_number]
            if step_number < len(propagation_steps):
                step = set(propagation_steps[step_number])
            else:
                step = set(propagation_steps[-1])
            
            pos = nx.spring_layout(G, seed=42)
            non_infected_nodes = set(G.nodes()) - step
            infected_nodes = step
            
            node_sizes_non_infected = [100 if G.nodes[n].get('authority') else 10 for n in non_infected_nodes]
            node_sizes_infected = [100 if G.nodes[n].get('authority') else 10 for n in infected_nodes]
            
            nx.draw_networkx_nodes(G, pos, nodelist=non_infected_nodes, node_color='blue', node_size=node_sizes_non_infected, ax=ax)
            nx.draw_networkx_nodes(G, pos, nodelist=infected_nodes, node_color='red', node_size=node_sizes_infected, ax=ax)
            nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5)
            
            ax.set_title(f"{network_translation[network_type]} (Step {step_number})", fontsize=10)
            ax.axis('off')
    
    plt.tight_layout()
    return fig

# Example usage
node_size = 200
network_types = ['erdos_renyi', 'watts_strogatz', 'barabasi_albert', 'complete', 'star']
steps = 5
clusters = 2

fig = plot_all_steps_single_page(network_types, node_size, steps, clusters)

with PdfPages(f'network_propagation_clusters_{clusters}.pdf') as pdf:
    pdf.savefig(fig)
    
    
def collect_messages_data(network_types, node_sizes, clusters_options=[1], simulations_per_setup=10):
    results = []
    for network_type in network_types:
        for n in node_sizes:
            for clusters in clusters_options:
                messages = []
                for _ in range(simulations_per_setup):
                    # Always use generate_network_with_authority for consistency
                    G = generate_network_with_authority(network_type, n, clusters=clusters)
                    _, total_messages = simulate_SI_model_with_authority(G, [list(G.nodes())[0]])
                    messages.append(total_messages)
                avg_messages = np.mean(messages)
                results.append({'Network Type': network_type, 'Nodes': n, 'Clusters': clusters, 'Average Messages': avg_messages})
    return results

def plot_messages_vs_nodes(results, filename='plot.png'):
    df_results = pd.DataFrame(results)
    plt.figure(figsize=(10, 8))
    for network_type in network_types:
        for clusters in df_results['Clusters'].unique():
            subset = df_results[(df_results['Network Type'] == network_type) & (df_results['Clusters'] == clusters)]
            plt.plot(subset['Nodes'], subset['Average Messages'], marker='o', linestyle='-', label=f"{network_translation[network_type]}, Clusters: {clusters}")
    
    plt.xlabel('Number of Nodes')
    plt.ylabel('Average Number of Messages Sent')
    plt.title('Average Number of Messages Sent vs. Number of Nodes')
    plt.legend(loc='upper left', frameon=True)
    plt.grid(True)
    
    # Save the figure to a file
    plt.savefig(filename)
    # Optionally display the plot
    plt.show()

# Assuming the rest of your code and the necessary imports are defined above
node_sizes = list(range(10, 1500, 100))
clusters_options = [0]  # Include 0 and 1 to test non-clustered and minimally-clustered networks
simulations_per_setup = 3  # Adjust based on the desired number of simulations per network setup

results = collect_messages_data(network_types, node_sizes, clusters_options, simulations_per_setup)
plot_messages_vs_nodes(results, 'network_messages_plot.pdf')



# Simplified function to fetch and process prices
def fetch_prices(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    data = requests.get(url).json()['prices']
    timestamps, prices = zip(*[(datetime.fromtimestamp(p[0] / 1000), p[1]) for p in data])
    return timestamps, prices

# Fetch prices
btc_timestamps, btc_prices = fetch_prices('bitcoin')
eth_timestamps, eth_prices = fetch_prices('ethereum')

# Plotting setup
fig, ax1 = plt.subplots(figsize=(8, 6))
ax2 = ax1.twinx()
ax1.set_xlabel('Date')
ax1.set_ylabel('BTC Price (USD)', color='tab:blue')
ax2.set_ylabel('ETH Price (USD)', color='tab:orange')

# Plot data
ax1.plot(btc_timestamps, btc_prices, label='BTC Price', color='tab:blue')
ax2.plot(eth_timestamps, eth_prices, label='ETH Price', color='tab:orange')

# Format date
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
fig.autofmt_xdate()

# Mark events
events = {datetime(2024, 2, 24): 'Red Sea Cable Cut', datetime(2024, 3, 5): 'News Release of the Event'}
for date, label in events.items():
    ax1.axvline(x=date, color='red', linestyle='--')
    ax1.text(date, ax1.get_ylim()[1] * 0.95, label, rotation=45, verticalalignment='top')

# Highlight price drop after the second date
second_date = datetime(2024, 3, 5) - timedelta(days=5)  # Adjusted for pre-event window
index = next(i for i, ts in enumerate(btc_timestamps) if ts >= second_date)
drops_indices = np.where(np.diff(btc_prices[index:]) < 0)[0]
if drops_indices.size > 0:
    closest_drop_date = btc_timestamps[index + drops_indices[0]]
    ax1.axvspan(closest_drop_date, closest_drop_date + timedelta(days=1), color='red', alpha=0.3)

fig.legend(loc='upper left', bbox_to_anchor=(0, 1), bbox_transform=ax1.transAxes, frameon=True)
fig.savefig('price_comparison_with_cable_event.pdf')
plt.show()