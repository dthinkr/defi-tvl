# TVL Value Transfers Network

This shows the token transfers across different DeFi protocols

- node size represent the state of the protocol before change
- edge size represent the inbound/outbound value changes of the protocol in the upcoming period (day)

## Note

This only records the changes, which means the network will not show nodes if they do not experience either inbound or outbound transfers.

```js
import { require } from "npm:d3-require";
// const d3 = require("d3@6");
var nw = FileAttachment("./data/fandoms2010-10.json").json(); 
const data = FileAttachment("./data/network_data.json").json();
```

```js

const parseTime = d3.timeParse("%Y-%m-%d");
const parseTimeDay = d3.timeParse("%Y-%m-%d");
const formatTime = d3.timeFormat("%B %d, %Y");
const formatMonth = d3.timeFormat("%Y-%m");
const formatMonthDay = d3.timeFormat("%Y-%m-%d");
const timemin = d3.min(data.links.map(d => parseTime(d.Date)));
const timemax = d3.max(data.links.map(d => parseTime(d.Date)));
const centrality = "degree_";
const numberOfDays = d3.timeDay.count(timemin, timemax);
const timeScale = d3.scaleTime()
  .domain([timemin, timemax])
	.range([0, numberOfDays]);

const windowspan = 2;
const date_compare = timeScale.invert(numberOfDays);
const datewindow = timeScale.invert(numberOfDays - windowspan);
const modularity_count = d3.max(data.nodes, d => d.modularity);

const edgeSize = d3.scaleLinear()
  .domain([d3.min(data.links, d => d.size), d3.max(data.links, d => d.size)])
  .range([0.1, 10]);

const tooltip = d3
  .select("body")
  .append("div")
  .style("position", "absolute") 
  .style("visibility", "hidden") 
  .style("background-color", "white")
  .attr("class", "tooltip");
const tooltip_in = function(event, d) { 
  return tooltip
    .html("<h4>" + d.id + "</h4>")
    .style("visibility", "visible") 
    .style("top", event.pageY + "px")
    .style("left", event.pageX + "px"); 
};
const tooltip_out = function() {
  return tooltip
    .transition()
    .duration(50) 
    .style("visibility", "hidden");
};
const nodeMin = 2;
const nodeMax = 30;
const height = 900;
const degreeSize = d3
  .scaleLinear()
  .domain([
    d3.min(data.nodes, function(d) {
      return d.degree;
    }),
    d3.max(data.nodes, function(d) {
      return d.degree;
    })
  ])
  .range([nodeMin, nodeMax]);

const color = (() => {
  const scale = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, modularity_count));
  return d => scale(d.modularity);
})();

const drag = simulation => {
  
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
  
  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
};

const zoom = container => {
  function zoomed(event, d) {
      container.attr("transform", "translate(" + event.transform.x + ", " + event.transform.y + ") scale(" + event.transform.k + ")");
  }
  
  return d3.zoom().on('zoom', zoomed)
};

const simulation = d3
  .forceSimulation()
  .force(
    "link",
    d3.forceLink().id(function(d) {
      return d.id;
    })
  )
  .force(
    "charge",
    d3
      .forceManyBody()
      .strength([-250])
      .distanceMax([500])
  )
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force(
    "collide",
    d3.forceCollide().radius(function(d) {
      return degreeSize(d.degree);
    })
  );
const links = data.links.filter(
      l => (parseTime(l.Date) <= date_compare) && (parseTime(l.Date) >= datewindow)         
    );
```

<!-- ```js
display(formatTime)
``` -->

```js
function slider(){
  let slider = html`
    <label for="threshold" style="width:25%;display:inline-block">Date: ${formatTime(
      timeScale.invert(numberOfDays)
    )}</label>
    <input type="range" min="0" max="${numberOfDays}" style="width:100%;display:inline-block"></input>`;
  let label = slider.querySelector('label');
  let range = slider.querySelector('input');
  range.value = numberOfDays;
  range.oninput = () => {
    let threshold = range.valueAsNumber;
    label.innerHTML = `Date: ${formatTime(timeScale.invert(threshold))}`;
  
    var c_value = formatMonthDay(timeScale.invert(threshold));
    var centrality_value = centrality + c_value;
    var date_compare = formatMonthDay(timeScale.invert(threshold));
    var datewindow = formatMonthDay(timeScale.invert(threshold-windowspan))
  
    var centralitySize = d3
      .scaleLinear()
      .domain([
        d3.min(data.nodes, function(d) {
          return d[centrality_value];
        }),
        d3.max(data.nodes, function(d) {
          return d[centrality_value];
        })
      ])
      .range([nodeMin, nodeMax]);
  
    d3.selectAll(".node")
      .attr("r", d => centralitySize(d[centrality_value]))
      .transition()
      .duration(300);
  
    let newLinks = data.links.filter(
      l => (parseTime(l.Date) <= parseTime(date_compare)) && (parseTime(l.Date) >= parseTime(datewindow))
    );
    chart.update(data.nodes, newLinks);
  };
  return slider;
}

function chart(data) {
  var threshold = 25
  var date_compare = formatMonthDay(timeScale.invert(threshold));
  var datewindow = formatMonthDay(timeScale.invert(threshold-windowspan))
  const links = data.links.filter(
      l => (parseTime(l.Date) <= parseTimeDay(date_compare)) && (parseTime(l.Date) >= parseTimeDay(datewindow))
    );
  console.log(parseTimeDay(datewindow), parseTimeDay(date_compare))
  const nodes = data.nodes.map(d => Object.create(d));
  const svg = d3.select(document.body)
    .append("svg")
    .attr("width", width)
    .attr("height", height);
  svg
    .append('rect')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('fill', 'white')
    .on('click', function() {
      d3.selectAll('.link').style('opacity', '1');
      d3.selectAll('.node').style('opacity', '1');
    });

  const defs = svg.append("defs");


  defs
    .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 8)
      .attr("refY", 5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto-start-reverse")
    .append("path")
      .attr("d", "M 0 0 L 10 5 L 0 10 z")
      .style("fill", "gray");

  var container = svg.append('g');

  svg.call(zoom(container));

  var link = container
    .append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(data.links)
    .enter()
    .append("line")
    .attr('class', 'link')
    .attr('stroke', 'gray')
    .attr('stroke-width', d => edgeSize(d.size));

  var node = container
    .append("g")
    .attr("class", "nodes")
    .selectAll("circle");

  // Make object of all neighboring nodes.
  let toggle = 0;
  var linkedByIndex = {};

  // keep the clicked node in linkedByIndex
  for (let i = 0; i < nodes.length; i++) {
    linkedByIndex[i + "," + i] = 1;
  }

  // Get the neighboring nodes and put them in linkedByIndex
  data.links.forEach(function(d) {
    linkedByIndex[d.source.index + ',' + d.target.index] = 1;
    linkedByIndex[d.target.index + ',' + d.source.index] = 1;
  });

  // A function to test if two nodes are neighboring.
  function neighboring(a, b) {
    return linkedByIndex[a.index + ',' + b.index];
  }

  function connectedNodes() {
    if (toggle == 0) {
      let d = d3.select(this).node().__data__;
      var neighbors = [];
      node.style("opacity", function(o) {
        neighboring(d, o) || neighboring(o, d) ? neighbors.push(o.id) : null;
        return neighboring(d, o) || neighboring(o, d) ? 1 : 0.15;
      });
      link.style("opacity", function(o) {
        return o.target == d || o.source == d ? 1 : 0.15;
      });
      var contents = [];
      neighbors.forEach(function(item) {
        contents.push("<li>" + item + "</li>");
      });
      // console.log(contents);
      return tooltip.html(
        // style the contents of your tooltip here.  This will replace the hover tooltip contents in tooltip below
        "<h4>" + d.id + "</h4><ul>" + contents.join("") + "</ul>"
      );

      toggle = 1;
    } else {
      link.style("opacity", 1);
      node.style("opacity", 1);
      toggle = 0;
    }
  }

  return Object.assign(svg.node(), {
    update(nodes, links) {
      // Update function code...
      link = link.data(links, function(d) {
        return d.source.index + ", " + d.target.index;
      });

      link.exit().remove();

      var linkEnter = link
        .enter()
        .append("line")
        .attr('class', 'link')
        .attr('stroke', 'gray')
        .attr('stroke-width', d => edgeSize(d.size)); 

      link = linkEnter.merge(link);

      node = node.data(nodes);

      node.exit().remove();

      var c_value = formatMonth(timemax);
      // console.log(c_value);
      var centrality_value = centrality + c_value;
      var nodeEnter = node
        .enter()
        .append("circle")
        .attr('r', function(d, i) {
          return degreeSize(d.degree);
        })
        .attr("fill", color)
        .attr('class', 'node')
        .on("mouseover", (event, d) => tooltip_in(event, d))
        .on("mouseout", tooltip_out)
        .on('click', connectedNodes)
        .call(drag(simulation));

      node = nodeEnter.merge(node);

      simulation.nodes(nodes).on("tick", ticked);

      simulation.force("link").links(links);

      simulation.alpha(1).restart();

  function ticked() {
    link
      .attr("x1", function(d) {
        return d.source.x;
      })
      .attr("y1", function(d) {
        return d.source.y;
      })
      .attr("x2", function(d) {
        return d.target.x;
      })
      .attr("y2", function(d) {
        return d.target.y;
      })
      .attr("marker-end", function(d) {
        // Determine the direction of the arrow based on source and target
        return (d.source.id < d.target.id) ? "url(#arrowhead)" : ""; // Add arrow if source id is less than target id
      });

    node
      .attr("cx", function(d) {
        return d.x;
      })
      .attr("cy", function(d) {
        return d.y;
      });
  }
      }
    });
  }
```

```html
<style type="text/css">
  .tooltip {
    fill: white;
    font-family: sans-serif;
    padding: .5rem;
    border-radius: 8px;
    border: 1px solid grey;
  }

</style>
```

```js
const myChart = chart(data); 
myChart.update(data.nodes, links);
display(slider());
display(myChart);
```

## Debugging:

```js
display(data);
display(nw);
```
