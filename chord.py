import streamlit as st
import numpy as np
import json

# Generate synthetic data for the chord diagram
def create_synthetic_data():
    matrix = np.random.randint(1, 100, (5, 5)).tolist()
    return matrix

data = create_synthetic_data()

# Convert the data to JSON format
json_data = json.dumps(data)

# HTML and JavaScript for the D3.js chord diagram
html_string = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://d3js.org/d3.v5.min.js"></script>
</head>
<body>
    <div id="chart"></div>
    <script>
        var matrix = {json_data};

        var width = 450,
            height = 450,
            innerRadius = width / 2 - 120,
            outerRadius = innerRadius + 10;

        // Create the SVG container for the chord diagram and set its dimensions
        var svg = d3.select("#chart").append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

        // Create the layout for the chord diagram
        var chord = d3.chord()
            .padAngle(0.05)
            .sortSubgroups(d3.descending)(matrix);

        // Create the groups (outer arcs)
        var group = svg.append("g")
            .selectAll("g")
            .data(chord.groups)
            .enter().append("g");

        group.append("path")
            .style("fill", "grey")
            .style("stroke", "black")
            .attr("d", d3.arc()
                .innerRadius(innerRadius)
                .outerRadius(outerRadius));

        // Create the ribbons (inner chords)
        svg.append("g")
            .selectAll("path")
            .data(chord)
            .enter().append("path")
            .attr("d", d3.ribbon()
                .radius(innerRadius))
            .style("fill", "blue")
            .style("stroke", "black");

    </script>
</body>
</html>
"""

# Use Streamlit's HTML component to render the chord diagram
st.markdown(html_string, unsafe_allow_html=True)
