```js
var protocol_data = FileAttachment("./data/protocol.csv").csv()
import * as Plot from "npm:@observablehq/plot";
import {require} from "npm:d3-require";
```


```js
const dfd = require("danfojs@1.0.5/lib/bundle.js").catch(() => {
  window.dfd.Series.prototype.print = window.dfd.DataFrame.prototype.print = function () {
    return print(this);
  };
  return window.dfd;
})
```


```js
const topX = 10
```

```js
async function aggregateAndVisualize(data) {
  let df = new dfd.DataFrame(data);
  
  // Step 1: Aggregate total values for each token
  let groupedDf = df.groupby(["token_name"]).agg({ "usd": ["sum"] });
  let sortedDf = groupedDf.sortValues("usd_sum", { ascending: false });
  
  // Step 2: Identify top X tokens
  let topXNames = sortedDf.head(topX)["token_name"].values;
  
  // Step 3: Mark all non-top X tokens as "Other"
  df["token_name"] = df["token_name"].apply((val) => {
    return topXNames.includes(val) ? val : "Other";
  });
  
  // Step 4: Aggregate again if necessary, for example, by date and token_name
  let finalGrouped = df.groupby(["aggregated_date", "token_name"]).agg({ "usd": ["sum"] });
  
  return finalGrouped.data;
}

// Assuming `data` is your dataset
var protocol_date = aggregateAndVisualize(protocol_data);
```

```js
Plot.plot({
  title: "Token Value Locked Over Time",
  marks: [
    Plot.areaY(processedData, Plot.stackY({
      x: "aggregated_date", 
      y: "usd", // Correct field for USD amount
      fill: "token_name", // Color by token name
      order: "appearance" // Order by appearance for clarity
    })),
    Plot.ruleY([0])
  ],
  color: {
    legend: true, 
    domain: processedData.map(d => d.token_name), 
    range: d3.schemeTableau20
  },
  x: {
    label: "Date",
    type: "utc", // Assuming dates are in UTC format
    grid: true
  },
  y: {
    label: "USD",
    grid: true
  },
  width: 800,
  height: 400
})
```

```js
Inputs.table(processedData)
```

