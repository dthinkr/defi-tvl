from itertools import chain
import pandas as pd
import networkx as nx
import altair as alt

# Step 1: Prepare an example graph (this all happens outside of Altair)

# example graph 
r,h = 3,3
G = nx.generators.classic.balanced_tree(r,h)

# calculate rank of a given node and assign it as data
for rank in range(0,h+1):
    nodes_in_rank = nx.descendants_at_distance(G, 0, rank)
    for node in nodes_in_rank: 
        G.nodes[node]['rank'] = rank

# calculate layout positions, for example using Graphviz's 'twopi' algorithm, calculated via networkx's API.  
pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='twopi')


# Step 2: Convert graph data from NetworkX's format to the pandas DataFrames expected by Altair

pos_df = pd.DataFrame.from_records(dict(node_id=k, x=x, y=y) for k,(x,y) in pos.items())
node_df = pd.DataFrame.from_records(dict(data, **{'node_id': n}) for n,data in G.nodes.data())
edge_data = ((dict(d, **{'edge_id':i, 'end':'source', 'node_id':s}),
              dict(d, **{'edge_id':i, 'end':'target', 'node_id':t}))
             for i,(s,t,d) in enumerate(G.edges.data()))
edge_df = pd.DataFrame.from_records(chain.from_iterable(edge_data))


# Step 3:  Use Altair to encode the graph data as marks in a visualization
x,y = alt.X('x:Q', axis=None), alt.Y('y:Q', axis=None)
# use a lookup to tie position data to the other graph data
node_position_lookup = {
    'lookup': 'node_id', 
    'from_': alt.LookupData(data=pos_df, key='node_id', fields=['x', 'y'])
}
nodes = (
    alt.Chart(node_df)
    .mark_circle(size=300, opacity=1)
    .encode(x=x, y=y, color=alt.Color('rank:N', legend=None))
    .transform_lookup(**node_position_lookup)
)
edges = (
    alt.Chart(edge_df)
    .mark_line(color='gray')
    .encode(x=x, y=y, detail='edge_id:N')  # `detail` gives one line per edge
    .transform_lookup(**node_position_lookup)
)
chart = (
    (edges+nodes)
    .properties(width=500, height=500,)
    .configure_view(strokeWidth=0)
)
chart