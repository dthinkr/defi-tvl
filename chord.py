import pandas as pd
import numpy as np
import holoviews as hv
from holoviews import opts, dim
import streamlit as st
hv.extension('bokeh')

def create_synthetic_data():
    # Synthetic Nodes Data
    nodes = pd.DataFrame({
        'index': range(5),  # Explicit numeric index
        'name': ['Node1', 'Node2', 'Node3', 'Node4', 'Node5'],
        'value': [10, 20, 30, 40, 50]
    }).set_index('index')  # Setting the 'index' column as the DataFrame index

    # Synthetic Links Data
    links = pd.DataFrame({
        'source': np.random.choice(nodes.index, 10),  # Using numeric indices
        'target': np.random.choice(nodes.index, 10),
        'value': np.random.randint(1, 10, 10)
    })

    return nodes, links

def display_chord_diagram():
    nodes, links = create_synthetic_data()

    # Debugging: Check data types and values
    print("Nodes DataFrame:pip install bokeh==2.4.0\n", nodes)
    print("Links DataFrame:\n", links)

    # Create HoloViews Dataset objects
    hv_nodes = hv.Dataset(nodes, 'index')
    hv_links = hv.Dataset(links, ['source', 'target'])

    # Create Chord object
    chord = hv.Chord((hv_links, hv_nodes)).opts(
        opts.Chord(
            cmap='Category20', edge_cmap='Category20', 
            labels='name', edge_color=dim('source').str()
        )
    )

    # Render and display the chord diagram in Streamlit
    st.subheader('Synthetic Chord Diagram')
    chord_diagram = hv.render(chord, backend='bokeh')
    st.bokeh_chart(chord_diagram)

# Main function of the Streamlit app
def main():
    st.title('Your App Title')
    # ... your existing code ...

    # Call to display the chord diagram
    display_chord_diagram()

# Run the Streamlit app
if __name__ == "__main__":
    main()
