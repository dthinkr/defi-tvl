# TVL Bar Race (TODO)
```js
import { require } from "npm:d3-require";
import * as d3 from "npm:d3";
import {csv, json} from "npm:d3-fetch";
const data2 = FileAttachment("./data/category-brands.csv").csv();
```

```js
const temp = Scrubber(keyframes, {
  // format: ([date]) => formatDate(date),
  delay: duration,
  loop: false
});

document.body.appendChild(temp); // Or append to another specific element if needed

let keyframe; // This will hold the current value of the scrubber

// Assuming the scrubber emits 'input' events and its value is accessible via `value` property
temp.addEventListener('input', () => {
  keyframe = temp.value; // Update the variable based on the scrubber's current value
  // Optionally, trigger any updates that depend on `keyframe`
});

display(temp);
display(keyframe);
```


```js
function chart() {
  const svg = d3.create("svg")
      .attr("viewBox", [0, 0, width, height])
      .style("background", "#1F0A21");
  
  const updateBars = bars(svg);
  //const updateAxis = axis(svg);
  const updateLabels = labels(svg);
  const updateTicker = ticker(svg);
  const updateRanks = ranks(svg);
  
  invalidation.then(() => svg.interrupt());

  return Object.assign(svg.node(), {
    update(keyframe) {
      const transition = svg.transition()
          .duration(duration)
          .ease(d3.easeLinear);

      // Extract the top bar’s value.
      x.domain([0, keyframe[1][0].value]);

      //updateAxis(keyframe, transition);
      updateBars(keyframe, transition);
      updateLabels(keyframe, transition);
      updateTicker(keyframe, transition);
      updateRanks(keyframe, transition);
      
    }
  });
}
```

```js
function bars(svg) {
  let bar = svg.append("g")
      .attr("fill-opacity", 1.0)   
    .selectAll("rect");

  return ([date, data], transition) => bar = bar
    .data(data.slice(0, n), d => d.name)
    .join(
      enter => enter
        .append("rect")
        .attr("fill", color)
        .attr("height", y.bandwidth())
        .attr("x", x(0))
        .attr("y", y(n))
        .attr("rx", 6)
        .attr("ry", 6)
        .attr("width", d => x(d.value) - x(0)),
      update => update,
      exit => exit.transition(transition).remove()
        //.attr("y", y(n))
        //.attr("width", d => x(d.value) - x(0))
    )
    .call(bar => bar.transition(transition)
      .attr("y", d => y(d.rank))
      .attr("width", d => x(d.value) - x(0)));
}

function ranks(svg) {
  let ranks = svg.append("g")
      .attr("fill-opacity", 1.0)  
      .style("font", "bold 17px var(--sans-serif)")
      //.style("font-variant-numeric", "tabular-nums")
      .style("fill", "white")
      .selectAll("text");
  
  return ([date, data], transition) => ranks = ranks
  .data(data.slice(0, n), d => d.rank) 
  .join(
      enter => enter
        .append("text")
         .text(d => d.rank + 1)
        //.attr("fill", "green")
        //.attr("height", y.bandwidth())
        .attr("x", x(0) - 36)
        .attr("y", d => y(d.rank)+26)
        //.attr("rx", 6)
        //.attr("ry", 6)
        .attr("width", 36),
      update => update,
      exit => exit
    )
}

function labels(svg) {
  let label = svg.append("g")
      .style("font", "bold 12px var(--sans-serif)")
      .style("font-variant-numeric", "tabular-nums")
      .style("fill", "white")
      .attr("text-anchor", "end"+10)
      
    .selectAll("text");
   
  return ([date, data], transition) => label = label
    .data(data.slice(0, n), d => d.name)
    .join(
      enter => enter.append("text")
        .attr("transform", d => `translate(${x(d.value)},${y(n)})`)
        .attr("y", y.bandwidth() / 2)
        .attr("x", 5)
        .attr("dy", "-0.25em")
        .text(d => d.name)
        .call(text => text.append("tspan")
          .attr("fill-opacity", 0.7)
          .attr("font-weight", "normal")
          .attr("x", 5)
          .attr("dy", "1.15em")),
      update => update,
      exit => exit.transition(transition).remove()
        .attr("transform", d => `translate(${x(d.value)},${y(n)})`)
    )
    .call(bar => bar.transition(transition)
      .attr("transform", d => `translate(${x(d.value)},${y(d.rank)})`)
      .call(g => g.select("tspan").tween("text", function(d) {
          return textTween(parseNumber(this.textContent), d.value);
        })));
}

function textTween(a, b) {
  const i = d3.interpolateNumber(a, b);
  return function(t) {
    this.textContent = formatNumber(i(t));
  };
}

function axis(svg) {
  const g = svg.append("g")
      //.attr("transform", `translate(0,${margin.top})`);

  const axis = d3.axisTop(x)
      .ticks(width / 160)
      .tickSizeOuter(0)
      .tickSizeInner(-barSize * (n + y.padding()));

  return (_, transition) => {
    g.transition(transition).call(axis);
    g.select(".tick:first-of-type text").remove();
    g.selectAll(".tick:not(:first-of-type) line")
      .attr("stroke", "white")
      .attr("stroke-opacity", 0.5);
    g.select(".domain").remove();
  };
}

function ticker(svg) {
  const now = svg.append("text")
      .style("font", `bold ${barSize}px var(--sans-serif)`)
      .style("font-variant-numeric", "tabular-nums")
      .attr("text-anchor", "end")
      .attr("x", width - 6)
      .attr("y", margin.top + barSize * (n - 0.45))
      .attr("dy", "0.32em")
      .text(formatDate(keyframes[0][0]));

  return ([date], transition) => {
    transition.end().then(() => now.text(formatDate(date)));
  };
}


```

```js
const datevalues = Array.from(d3.rollup(data, ([d]) => d.value, d => +d.date, d => d.name))
  .map(([date, data]) => [new Date(date), data])
  .sort(([a], [b]) => d3.ascending(a, b));

function keyframes() {
  const keyframes = [];
  let ka, a, kb, b;
  for ([[ka, a], [kb, b]] of d3.pairs(datevalues)) {
    for (let i = 0; i < k; ++i) {
      const t = i / k;
      keyframes.push([
        new Date(ka * (1 - t) + kb * t),
        rank(name => a.get(name) * (1 - t) + b.get(name) * t)
      ]);
    }
  }
  keyframes.push([new Date(kb), rank(name => b.get(name))]);
  return keyframes;
}

function rank(value) {
  const data = Array.from(names, name => ({name, value: value(name) || 0}));
  data.sort((a, b) => d3.descending(a.value, b.value));
  for (let i = 0; i < data.length; ++i) data[i].rank = Math.min(n, i);
  return data;
}
```

```js
function Scrubber(values, {
  format = value => value,
  initial = 0,
  direction = 1,
  delay = null,
  autoplay = true,
  loop = true,
  loopDelay = null,
  alternate = false
} = {}) {
  values = Array.from(values);
  const form = html`<form style="font: 12px var(--sans-serif); font-variant-numeric: tabular-nums; display: flex; height: 33px; align-items: center;">
  <button name=b type=button style="margin-right: 0.4em; width: 5em;"></button>
  <label style="display: flex; align-items: center;">
    <input name=i type=range min=0 max=${values.length - 1} value=${initial} step=1 style="width: 180px;">
    <output name=o style="margin-left: 0.4em;"></output>
  </label>
</form>`;
  let frame = null;
  let timer = null;
  let interval = null;
  function start() {
    form.b.textContent = "Pause";
    if (delay === null) frame = requestAnimationFrame(tick);
    else interval = setInterval(tick, delay);
  }
  function stop() {
    form.b.textContent = "Play";
    if (frame !== null) cancelAnimationFrame(frame), frame = null;
    if (timer !== null) clearTimeout(timer), timer = null;
    if (interval !== null) clearInterval(interval), interval = null;
  }
  function running() {
    return frame !== null || timer !== null || interval !== null;
  }
  function tick() {
    if (form.i.valueAsNumber === (direction > 0 ? values.length - 1 : direction < 0 ? 0 : NaN)) {
      if (!loop) return stop();
      if (alternate) direction = -direction;
      if (loopDelay !== null) {
        if (frame !== null) cancelAnimationFrame(frame), frame = null;
        if (interval !== null) clearInterval(interval), interval = null;
        timer = setTimeout(() => (step(), start()), loopDelay);
        return;
      }
    }
    if (delay === null) frame = requestAnimationFrame(tick);
    step();
  }
  function step() {
    form.i.valueAsNumber = (form.i.valueAsNumber + direction + values.length) % values.length;
    form.i.dispatchEvent(new CustomEvent("input", {bubbles: true}));
  }
  form.i.oninput = event => {
    if (event && event.isTrusted && running()) stop();
    form.value = values[form.i.valueAsNumber];
    form.o.value = format(form.value, form.i.valueAsNumber, values);
  };
  form.b.onclick = () => {
    if (running()) return stop();
    direction = alternate && form.i.valueAsNumber === values.length - 1 ? -1 : 1;
    form.i.valueAsNumber = (form.i.valueAsNumber + direction) % values.length;
    form.i.dispatchEvent(new CustomEvent("input", {bubbles: true}));
    start();
  };
  form.i.oninput();
  if (autoplay) start();
  else stop();
  Inputs.disposal(form).then(stop);
  return form;
}

```


```js
// chart.update(keyframe);
const formatDate = d3.utcFormat("%Y");
const duration = 250;
const n = 100;
const names = new Set(data.map(d => d.name));
const k = 10;

// const nameframes = d3.groups(keyframes.flatMap(([, data]) => data), d => d.name);
var parseNumber = string => +string.replace(/,/g, "");
var formatNumber = d3.format(",d");
var color = "#3B1A48";
var margin = ({top: 16, right: 76, bottom: 6, left: 40});
var x = d3.scaleSqrt([0, 1], [margin.left, width - margin.right]);
var y = d3.scaleBand()
    .domain(d3.range(n + 1))
    .rangeRound([margin.top, margin.top + barSize * (n + 1 + 0.1)])
    .padding(0.09);
var height = margin.top + barSize * n + margin.bottom;
var barSize = 36;  
```
```js
const data = data2.map(row => {
  return {...row, date: new Date(row.date)}
})
```


## Debugging:

```js
display(datevalues);
display(data);
display(data2);
display(names);
```