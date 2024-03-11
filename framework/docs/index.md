---
toc: false
---

<style>

:root {
  --theme-foreground-focus: #ffb71a; /* New red color */
  /* --theme-foreground-muted: #ffb71a; Softer red */
}

.hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: var(--sans-serif);
  margin: 4rem 0 8rem;
  text-wrap: balance;
  text-align: center;
}

.hero h1 {
  margin: 2rem 0;
  max-width: none;
  font-size: 14vw;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(0deg, var(--theme-foreground-focus), currentColor);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero h2 {
  margin: 0;
  max-width: 34em;
  font-size: 20px;
  font-style: initial;
  font-weight: 500;
  line-height: 1.5;
  color: var(--theme-foreground-muted);
}

@media (min-width: 640px) {
  .hero h1 {
    font-size: 90px;
  }
}

</style>

<div class="hero">
  <h1>TVL Data</h1>
  <h2>A set of data dashboards for DeFi protocols and tokens.</h2>
  <a href="https://defillama.com/" target="_blank">Source<span style="display: inline-block; margin-left: 0.25rem;">↗︎</span></a>
</div>

<div class="grid grid-cols-2" style="grid-auto-rows: auto">
  <div class="card">${
    resize((width) => Plot.plot({
      title: "Historical TVL",
      subtitle: "$ billions",
      width,
      y: {grid: true, label: "Ethereum"},
      x: {
        tickFormat: d3.timeFormat("%Y"),
      },
      marks: [
        Plot.ruleY([0]),
        Plot.lineY(eth.map(d => ({...d, tvl: d.tvl / 1e9})), {x: "date", y: "tvl", tip: true})
      ]
    }))
  }</div>


<div class="card" style="grid-auto-rows: auto;">    
<h2>TVL Transfer Intensity in 2023</h2>
    <h3>$ billions</h3>
    ${Plot.cell(all.filter(d => {
      const date = new Date(d.date); // Directly use YMD string to create a Date object
      return date.getFullYear() === 2023;
    }), {x: (d) => {
      const date = new Date(d.date);
      return date.getUTCDate();
    }, y: (d) => {
      const date = new Date(d.date);
      return date.getUTCMonth();
    }, fill: "tvl", tip: true, inset: 0.5}).plot({marginTop: 0, marginBottom: -50, padding: 0, height: 425})}
</div>
</div>


```js
const eth = FileAttachment("./data/frontpage_line.csv").csv({typed: true});
const all = FileAttachment("./data/frontpage_heat.csv").csv({typed: true});
```