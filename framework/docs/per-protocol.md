# TVL Per Protocol

```js
var protocol_data = FileAttachment("./data/protocol_data.csv").csv()
var protocol_name = FileAttachment("./data/protocol_name.csv").csv()
import * as Plot from "npm:@observablehq/plot";
import {require} from "npm:d3-require";
import papaparse from "https://cdn.skypack.dev/papaparse@5.3.2";
```

```js
const protocol = view(
  Inputs.select(
    protocol_name.columns.map((name) => ({name: name})), // Map each name to an object with a name property
    {
      label: "Protocol",
      value: (d) => d.name, // Use the name property for the value
      format: (d) => d.name, // Use the name property for the display format
      sort: true,
      unique: true
    }
  )
)
```

```js
const dfd = require("danfojs@1.1.2/lib/bundle.js").catch(() => {
  window.dfd.Series.prototype.print = window.dfd.DataFrame.prototype.print = function () {
    return print(this);
  };
  return window.dfd;
})
```

```js
const topX = 20
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
  // Convert the DataFrame to a CSV string
  let csvString = dfd.toCSV(finalGrouped);
  // Parse the CSV string into an array of objects
  const parsedData = papaparse.parse(csvString, { header: true }).data;
  return parsedData;
}
```

```js
const processed_data = await aggregateAndVisualize(protocol_data);
```

```js
Plot.plot({
  title: "Token Value Locked Over Time",
  marks: [
    Plot.areaY(processed_data, Plot.stackY({
      x: "aggregated_date", 
      y: "usd_sum", // Correct field for USD amount
      fill: "token_name", // Color by token name
      order: "appearance" // Order by appearance for clarity
    })),
    Plot.ruleY([0])
  ],
  color: {
    legend: true, 
    domain: processed_data.map(d => d.token_name), 
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

## Debugging

The protocol name is

```js
display(protocol_name)
```

The protocol_data is

```js
Inputs.table(protocol_data);
display(protocol_data)
```

The processed_data is

```js
Inputs.table(processed_data);
display(processed_data);
```
