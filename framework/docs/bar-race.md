# TVL Bar Race (TODO)
```html
<style>
text{
  font-size: 15px;
  font-family: Open Sans, sans-serif;
}
text.title{
  font-size: 28px;
  font-weight: 600;
}
text.subTitle{
  font-weight: 500;
  fill: #777777;
}
text.label{
  font-size: 15px;
}
.map-legend text{
  font-size: 13px;
  fill: #777777;
}
text.caption{
  font-weight: 400;
  font-size: 13px;
  fill: #999999;
}
text.yearText{
  font-size: 84px;
  font-weight: 700;
  fill: #cccccc;
}
text.yearIntro{
  font-size: 44px;
  font-weight: 700;
  fill: #cccccc;
}
.tick text {
  fill: #777777;
}
.xAxis .tick:nth-child(2) text {
  text-anchor: start;
}
.tick line {
  shape-rendering: CrispEdges;
  stroke: #dddddd;
}
.tick line.origin{
  stroke: #aaaaaa;
}
path.domain{
  display: none;
}
</style>
```


```js
import { require } from "npm:d3-require";
// import * as jsdom from 'npm:jsdom'
import {DOM} from "npm:@observablehq/stdlib";
const d3 = require('d3-scale@2','d3-array@1','d3-fetch@1','d3-selection@1','d3-timer@1','d3-color@1','d3-format@1','d3-ease@1','d3-interpolate@2','d3-axis@2', 'd3-geo@1', 'd3-selection-multi@1');
const topojson = require('topojson-client@3', 'topojson-simplify@3');

const height = 890/(1920/1080);
const tickDuration = 250;
const top_n = 10;
const startYear = 1500;
const endYear = 2018;

const halo = function(text, strokeWidth, color='#ffffff') {
  text.select(function() { return this.parentNode.insertBefore(this.cloneNode(true), this); })
    .styles({
      fill: color,
      stroke: color,
      'stroke-width': strokeWidth,
      'stroke-linejoin': 'round',
      opacity: 1
    });
};

const haloHighlight = function(text, delay, strokeWidth=1, opacity=1, color='#000000') {
  let textObject = text.select(function() { return this.parentNode.insertBefore(this.cloneNode(true), this); })
    .styles({
      fill: '#ffffff',
      stroke: color,
      'stroke-width': 0,
      'stroke-linejoin': 'round',
      opacity: opacity
    });
  textObject
    .transition()
      .ease(d3.easeLinear)
      .delay(delay)
      .duration(250)
      .styles({
        'stroke-width': strokeWidth
      })
      .transition()
        .ease(d3.easeLinear)
        .delay(500)
        .duration(250)
        .styles({
          'stroke-width': 0
        });
};



```

```js
function chart (world, dataset) {
  const svg = d3.select(DOM.svg(width, height));
  
  const margin = {
    top: 70,
    right: 0,
    bottom: 10,
    left: 0
  };
  
  let barPadding = (height-(margin.bottom+margin.top))/(top_n*5);
  
  let title = svg.append('text')
    .attrs({
      class: 'title',
      y: 24
    })
    .html('The most populous cities in the world from 1500 to 2018');
  
  haloHighlight(title, 250, 2, 1, '#000000');
  
  let subTitle = svg.append('text')
    .attrs({
      class: 'subTitle',
      y: 48
    })
    .html('Population (thousands)');
  
  haloHighlight(subTitle, 1750, 1, 1, '#777777');

  let year = startYear;
  
  dataset.forEach(d => {
    d.value = +d.value,
    d.lastValue = +d.lastValue,
    d.value = isNaN(d.value) ? 0 : d.value,
    d.year = +d.year,
    // d.colour = d3.hsl(Math.random()*360,0.75,0.75)
    d.colour = "#C8BDFF"
  });
  
  let yearSlice = dataset.filter(d => d.year == year && !isNaN(d.value))
    .sort((a,b) => b.value - a.value)
    .slice(0,top_n);
  
  yearSlice.forEach((d,i) => d.rank = i);
  
  let x = d3.scaleLinear()
    .domain([0, d3.max(yearSlice, d => d.value)])
    .range([margin.left, width-margin.right-115]);
  
  let y = d3.scaleLinear()
    .domain([top_n, 0])
    .range([height-margin.bottom, margin.top]);
  
  let groups = dataset.map(d => d.group);
  groups = [...new Set(groups)];
  
  let colourScale = d3.scaleOrdinal()
    .range(["#adb0ff", "#ffb3ff", "#90d595", "#e48381", "#aafbff", "#f7bb5f", "#eafb50"])
    .domain(["India","Europe","Asia","Latin America","Middle East","North America","Africa"]);
    // .domain(groups);
  
  let xAxis = d3.axisTop()
    .scale(x)
    .ticks(width > 500 ? 5:2)
    .tickSize(-(height-margin.top-margin.bottom))
    .tickFormat(d => d3.format(',')(d));
  
  svg.append('g')
    .attrs({
      class: 'axis xAxis',
      transform: `translate(0, ${margin.top})`
    })
    .call(xAxis)
      .selectAll('.tick line')
      .classed('origin', d => d == 0);
  
  svg.selectAll('rect.bar')
    .data(yearSlice, d => d.name)
    .enter()
    .append('rect')
    .attrs({
      class: 'bar',
      x: x(0)+1,
      width: d => x(d.value)-x(0)-1,
      y: d => y(d.rank)+5,
      height: y(1)-y(0)-barPadding
    })
    .styles({
      fill: d => colourScale(d.group)
      // fill: d => d.colour
    });
  
  svg.selectAll('text.label')
    .data(yearSlice, d => d.name)
    .enter()
    .append('text')
    .attrs({
      class: 'label',
      transform: d => `translate(${x(d.value)-5}, ${y(d.rank)+5+((y(1)-y(0))/2)-7})`,
      'text-anchor': 'end'
    })
    .selectAll('tspan')
    .data(d => [{text: d.name, opacity: 1, weight:600}, {text: d.subGroup, opacity: 1, weight:400}])
    .enter()
    .append('tspan')
    .attrs({
      x: 0,
      dy: (d,i) => i*15
    })
    .styles({
      // opacity: d => d.opacity,
      fill: d => d.weight == 400 ? '#444444':'',
      'font-weight': d => d.weight,
      'font-size': d => d.weight == 400 ? '11px':''
    })
    .html(d => d.text);
  
  svg.selectAll('text.valueLabel')
    .data(yearSlice, d => d.name)
    .enter()
    .append('text')
    .attrs({
      class: 'valueLabel',
      x: d => x(d.value)+5,
      y: d => y(d.rank)+5+((y(1)-y(0))/2)+1,
    })
    .text(d => d3.format(',.0f')(d.lastValue));
  
  let credit = svg.append('text')
    .attrs({
      class: 'caption',
      x: width,
      y: height-27
    })
    .styles({
      'text-anchor': 'end'
    })
    .html('Graphic: @jburnmurdoch')
    .call(halo, 10);
  
  let sources = svg.append('text')
    .attrs({
      class: 'caption',
      x: width,
      y: height-6
    })
    .styles({
      'text-anchor': 'end'
    })
    .html('Sources: Reba, M. L., F. Reitsma, and K. C. Seto. 2018; Demographia')
    .call(halo, 10);
  
  let yearIntro = svg.append('text')
    .attrs({
      class: 'yearIntro',
      x: width-191,
      y: height-175
    })
    .styles({
      'text-anchor': 'end'
    })
    .html('Year: ');
  
  yearIntro.call(halo, 10);
  
  haloHighlight(yearIntro, 3000, 3, 1, '#cccccc');
  
  let yearText = svg.append('text')
    .attrs({
      class: 'yearText',
      x: width-191,
      y: height-175
    })
    // .styles({
    //   'text-anchor': 'end'
    // })
    .html(~~year);
  
  yearText.call(halo, 10);
  
  haloHighlight(yearText, 3000, 8, 1, '#cccccc');
  
  let regions = world_simplified.objects.ne_10m_admin_0_countries.geometries.map(d => d.properties.REGION_WB);
  regions = [...new Set(regions)];
  
  const path = d3.geoPath()
    .projection(projection);
 
  let mapLegend = svg.append('g')
    .attrs({
      class: 'map-legend',
      transform: `translate(${width-191}, ${height-140})`
    });
  
  mapLegend
    .append('rect')
    .attrs({
      x: 0,
      y: -25,
      width: 190,
      height: 120
    })
    .styles({
      fill: '#ffffff',
      stroke: '#dddddd'
    });
  
  let mapSubtitle = mapLegend
    .append('text')
    .attrs({
      x: 5,
      y: -10
    })
    .html('Bar colours represent regions');

  mapSubtitle.call(halo, 5);
  
  haloHighlight(mapSubtitle, 4500, 1, 1, '#777777');
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'South Asia')))
    .attrs({
      d: path,
      fill: colourScale('India')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'East Asia & Pacific')))
    .attrs({
      d: path,
      fill: colourScale('Asia')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'Europe & Central Asia' && d.properties.ADMIN != 'Greenland')))
    .attrs({
      d: path,
      fill: colourScale('Europe')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'North America')))
    .attrs({
      d: path,
      fill: colourScale('North America')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'Middle East & North Africa')))
    .attrs({
      d: path,
      fill: colourScale('Middle East')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'Sub-Saharan Africa')))
    .attrs({
      d: path,
      fill: colourScale('Africa')
    });
  
  mapLegend
    .append('path')
    .datum(topojson.merge(world_simplified, world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => d.properties.REGION_WB == 'Latin America & Caribbean')))
    .attrs({
      d: path,
      fill: colourScale('Latin America')
    });
  
  mapLegend
    .selectAll('circle')
    .data(yearSlice, d => d.name)
    .enter()
    .append('circle')
    .attrs({
      class: 'cityMarker',
      cx: d => projection([d.lon, d.lat])[0],
      cy: d => projection([d.lon, d.lat])[1],
      r: 3
    })
    .styles({
      stroke: '#666666',
      fill: '#000000',
      'fill-opacity': 0.3
    });
  
  d3.timeout(_ => {
    
    svg.selectAll('.yearIntro')
      .transition()
      .duration(1000)
      .ease(d3.easeLinear)
      .styles({
        opacity: 0
      });
  
    let ticker = d3.interval(e => {

      yearSlice = dataset.filter(d => d.year == year && !isNaN(d.value))
        .sort((a,b) => b.value - a.value)
        .slice(0,top_n);

      yearSlice.forEach((d,i) => d.rank = i);

      x.domain([0, d3.max(yearSlice, d => d.value)]);

      svg.select('.xAxis')
        .transition()
        .duration(tickDuration)
        .ease(d3.easeLinear)
        .call(xAxis);

      let bars = svg.selectAll('.bar').data(yearSlice, d => d.name);

      bars
        .enter()
        .append('rect')
        .attrs({
          class: d => `bar ${d.name.replace(/\s/g,'_')}`,
          x: x(0)+1,
          width: d => x(d.value)-x(0)-1,
          y: d => y(top_n+1)+5,
          height: y(1)-y(0)-barPadding
        })
        .styles({
          fill: d => colourScale(d.group)
          // fill: d => d.colour
        })
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            y: d => y(d.rank)+5
          });

      bars
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            width: d => x(d.value)-x(0)-1,
            y: d => y(d.rank)+5
          });

      bars
        .exit()
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            width: d => x(d.value)-x(0)-1,
            y: d => y(top_n+1)+5
          })
          .remove();

      let labels = svg.selectAll('.label').data(yearSlice, d => d.name);

      labels
        .enter()
        .append('text')
        .attrs({
          class: 'label',
          transform: d => `translate(${x(d.value)-5}, ${y(top_n+1)+5+((y(1)-y(0))/2)-8})`,
          'text-anchor': 'end'
        })
        .html('')    
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            transform: d => `translate(${x(d.value)-5}, ${y(d.rank)+5+((y(1)-y(0))/2)-7})`
          });

      let tspans = labels
        .selectAll('tspan')
        .data(d => [{text: d.name, opacity: 1, weight:600}, {text: d.subGroup, opacity: 1, weight:400}]);

      tspans.enter()
        .append('tspan')
        .html(d => d.text)
        .attrs({
          x: 0,
          dy: (d,i) => i*15
        })
        .styles({
          // opacity: d => d.opacity,
          fill: d => d.weight == 400 ? '#444444':'',
          'font-weight': d => d.weight,
          'font-size': d => d.weight == 400 ? '11px':''
        });

      tspans
        .html(d => d.text)
        .attrs({
          x: 0,
          dy: (d,i) => i*15
        })
        .styles({
          // opacity: d => d.opacity,
          fill: d => d.weight == 400 ? '#444444':'',
          'font-weight': d => d.weight,
          'font-size': d => d.weight == 400 ? '11px':''
        });

      tspans.exit()
        .remove();

      labels
        .transition()
        .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            transform: d => `translate(${x(d.value)-5}, ${y(d.rank)+5+((y(1)-y(0))/2)-7})`
          });

      labels
        .exit()
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            transform: d => `translate(${x(d.value)-8}, ${y(top_n+1)+5})`
          })
          .remove();

      let valueLabels = svg.selectAll('.valueLabel').data(yearSlice, d => d.name);

      valueLabels
        .enter()
        .append('text')
        .attrs({
          class: 'valueLabel',
          x: d => x(d.value)+5,
          y: d => y(top_n+1)+5,
        })
        .html(d => d3.format(',.0f')(d.lastValue))
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            y: d => y(d.rank)+5+((y(1)-y(0))/2)+1
          });

      valueLabels
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            x: d => x(d.value)+5,
            y: d => y(d.rank)+5+((y(1)-y(0))/2)+1
          })
          .tween("text", function(d) {
            let i = d3.interpolateRound(d.lastValue, d.value);
            return function(t) {
              this.textContent = d3.format(',')(i(t));
            };
          });

      valueLabels
        .exit()
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            x: d => x(d.value)+5,
            y: d => y(top_n+1)+5
          })
          .remove();

      let cityMarkers = svg.select('.map-legend').selectAll('.cityMarker').data(yearSlice, d => d.name);

      cityMarkers
        .enter()
        .append('circle')
        .attrs({
          class: 'cityMarker',
          cx: d => projection([d.lon, d.lat])[0],
          cy: d => projection([d.lon, d.lat])[1],
          r: 0
        })
        .styles({
          stroke: '#000000',
          fill: 'none'
        })
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            r: 10
          });

      cityMarkers
        .attrs({
          class: 'cityMarker',
          cx: d => projection([d.lon, d.lat])[0],
          cy: d => projection([d.lon, d.lat])[1],
          r: 3
        })
        .styles({
          stroke: '#666666',
          fill: '#000000',
          'fill-opacity': 0.3
        })
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            r: 3
          });

      cityMarkers
        .exit()
        .transition()
          .duration(tickDuration)
          .ease(d3.easeLinear)
          .attrs({
            r: 0
          })
          .remove();

      yearText.html(~~year);

      if(year == endYear) ticker.stop();
      year = year + 1;
    },tickDuration);
  
  }, 6000);

  return svg.node();
}
```


```js
const world = await d3.json('https://gist.githubusercontent.com/johnburnmurdoch/b6a18add7a2f8ee87a401cb3055ccb7b/raw/f46c5c442c5191afc105b934b4b68c653545b7c1/ne_10m_simplified.json');

const dataset = await d3.csv('https://gist.githubusercontent.com/johnburnmurdoch/bdedaf6f17a8714d00dd66e6f48efe42/raw/4bec8da113c6908e026e91a4f2bc712193970b37/city_populations_projections.csv');

display(world);
display(dataset);

const world_simplified = (() => {
  let word_simplified = topojson.presimplify(world);
  let min_weight = topojson.quantile(word_simplified, 0.3);
  word_simplified = topojson.simplify(word_simplified, min_weight);
  
  let land = word_simplified;  
  
  return land;
})();

const land = topojson.feature(world_simplified, {
    type: 'GeometryCollection',
    geometries: world_simplified.objects.ne_10m_admin_0_countries.geometries.filter(d => ['Antarctica','Greenland'].includes(d.properties.ADMIN))
  });

const projection = d3.geoNaturalEarth1()
  .fitSize([185, 105], land);

```

```js

display(world_simplified)
```
```js
display(chart(world,dataset))
```
