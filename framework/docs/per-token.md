# TVL Per Token

```js
var token_data = FileAttachment("./data/token_data.csv").csv()
var flare = FileAttachment("./data/flare.json").json()
import { require } from "npm:d3-require";
const d3Hierarchy = require("d3-hierarchy");
const d3Scale = require("d3-scale");
const d3ScaleChromatic = require("d3-scale-chromatic");
const d3Selection = require("d3-selection");

```

```js
function area(data) {
  // Constants for configuration
    const cluster = 'type'
    const width = 800;
    const height = 800;
    const maxCells = 100; // Maximum number of cells per cluster
    const maxClusters = 10;
    const formatValue = d3.format(",.2s"); // Format for displaying values
    const legendWidth = 150; // New constant for legend width
    const legendHeight = 100;
    const totalWidth = width; 
    const totalHeight = height + legendHeight;
    const textSize = "12px";
    const minAreaForText = 12000;
    const tableau20 = [
    "#e15759", "#edc948", "#f28e2b", "#76b7b2", "#59a14f",
    "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#4e79a7", 
    "#d37295", "#fabfd2", "#b6992d", "#499894", "#86bcb6",
    "#f56476", "#a3a500", "#dcb0f2", "#882e72", "#9fd077"
    ];

    // Helper function to format large numbers
    const format = d => `${formatValue(d).replace('G', 'B')}`;

    // Step 1: Filter and Aggregate Data
    const latestDate = data.reduce((max, d) => d.aggregated_date > max ? d.aggregated_date : max, data[0].aggregated_date);
    const filteredData = data.filter(d => d.aggregated_date === latestDate);

    // Step 2: Prepare Hierarchical Data Structure
    const rootData = { name: "root", children: [] };
    const clusterMap = new Map();
    filteredData.forEach(d => {
    const clusterKey = d.type; // Assuming 'type' is your cluster key
    if (!clusterMap.has(clusterKey)) {
        clusterMap.set(clusterKey, { name: clusterKey, children: [] });
    }
    clusterMap.get(clusterKey).children.push({
        name: d.protocol_name,
        value: d.usd,
        aggregated_date: d.aggregated_date,
        chain_name: d.chain_name
    });
    });

    // Sort clusters based on total value and keep only the top maxClusters
    let clusters = Array.from(clusterMap.values()).sort((a, b) => 
        d3.sum(b.children, child => child.value) - d3.sum(a.children, child => child.value)
    ).slice(0, maxClusters);


    if(clusterMap.size > maxClusters) {
        const othersCluster = { name: `Combined ${cluster}`, children: []};
        Array.from(clusterMap.values()).slice(maxClusters).forEach(cluster => {
        othersCluster.children = othersCluster.children.concat(cluster.children);
        });
        clusters.push(othersCluster);
    }
  
    // Aggregate additional protocols into 'Others'
    rootData.children = clusters.map(cluster => {
        cluster.children.sort((a, b) => b.value - a.value); // Sort based on value
        if (cluster.children.length > maxCells) {
        const others = cluster.children.slice(maxCells).reduce((acc, curr) => acc + curr.value, 0);
        cluster.children = cluster.children.slice(0, maxCells);
        cluster.children.push({ name: "Others", value: others });
        }
        return cluster;
    });

    // Specify the color scale.
    const color = d3.scaleOrdinal(rootData.children.map(d => d.name), tableau20);
    // Compute the layout.
    const root = d3.treemap()
        .tile(d3.treemapSquarify) // or use another tiling method
        .size([width, height])
        .padding(2)
        .round(true)
        (d3.hierarchy(rootData)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value));

    // Create the SVG container.
    const svg = d3.create("svg")
        .attr("viewBox", [0, 0, totalWidth, totalHeight])
        .attr("width", totalWidth)
        .attr("height", totalHeight)
        .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

    // Add a cell for each leaf of the hierarchy.
    const leaf = svg.selectAll("g")
        .data(root.leaves())
        .join("g")
        .attr("transform", d => `translate(${d.x0},${d.y0})`);

    // Append a tooltip.
    leaf.append("title")
        .text(d => `${d.ancestors().reverse().map(d => d.data.name).join("/")}\n${format(d.value)}`);

    // Append a color rectangle.
    leaf.append("rect")
        .attr("fill", d => color(d.parent.data.name))
        .attr("fill-opacity", 0.6)
        .attr("width", d => d.x1 - d.x0)
        .attr("height", d => d.y1 - d.y0);

    leaf.append("text")
        .filter(d => (d.x1 - d.x0) * (d.y1 - d.y0) >= minAreaForText) // Check if the area is above the threshold
        .attr("x", 10)
        .attr("y", 20)
        .text(d => format(d.value))
        .attr("font-size", textSize)
        .attr("fill", "black");

    leaf.append("text")
        .filter(d => (d.x1 - d.x0) * (d.y1 - d.y0) >= minAreaForText) // Check if the area is above the threshold
        .attr("x", 10)
        .attr("y", 35)
        .text(d => d.data.name)
        .attr("font-size", textSize)
        .attr("font-weight", "bold") // Make text bold
        .attr("fill", "black");

    leaf.append("text")
        .attr("x", 10)
        .attr("y", 50) // Adjust this value based on your layout needs
        .filter(d => (d.x1 - d.x0) * (d.y1 - d.y0) >= minAreaForText) // Check if the area is above the threshold
        .text(d => d.data.aggregated_date) // Assuming 'aggregated_date' is the property name
        .attr("font-size", textSize)
        .attr("fill", "black");

    leaf.append("text")
        .attr("x", 10)
        .attr("y", 65) // Adjust this value based on your layout needs
        .filter(d => (d.x1 - d.x0) * (d.y1 - d.y0) >= minAreaForText) // Check if the area is above the threshold
        .text(d => d.data.chain_name) // Assuming 'aggregated_date' is the property name
        .attr("font-size", textSize)
        .attr("fill", "black");

    // Create the legend
    const itemsPerLine = Math.ceil(color.domain().length / 3); // Assuming you want 3 lines
    const legendSpacing = 25; // Vertical spacing between lines
    const itemWidth = 250; // Horizontal space each item takes
    const rightMargin = 20;
    const legendXPosition = totalWidth - rightMargin;

    const legend = svg.append("g")
        .attr("transform", `translate(${legendXPosition}, ${height+3})`) // Adjust to align right
        .attr("text-anchor", "end")
        .selectAll("g")
        .data(color.domain().slice().reverse())
        .join("g");

    legend.attr("transform", (d, i) => {
        const line = Math.floor(i / itemsPerLine); // Determine the line number
        const x = -(i % itemsPerLine) * itemWidth; // Adjust x position for right alignment
        const y = line * legendSpacing; // Adjust vertical position based on line number
        return `translate(${x}, ${y})`;
    });

    // Continue with appending rects and texts to each legend item as before
    legend.append("rect")
        .attr("y", 0)
        .attr("width", 19)
        .attr("height", 19)
        .attr("fill", color);

    legend.append("text")
        .attr("x", -5) // Adjust x position to align text next to the rectangle
        .attr("y", 9.5) // Center text vertically with the rectangle
        .attr("dy", "0.35em")
        .text(d => d);

    return svg.node();
}
```

This displays the most recent token data 

```js
display(area(token_data));
```

## Debugging:
```js
display(token_data)
```