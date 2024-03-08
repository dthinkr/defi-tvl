```js
var protocol_data = FileAttachment("./data/protocol.csv").csv()
import * as Plot from "npm:@observablehq/plot";
import {require} from "npm:d3-require";
import papaparse from "https://cdn.skypack.dev/papaparse@5.3.2";
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
const topX = 5
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
    Plot.stackY(
      Plot.groupX(
        {
          y: "sum",
          fill: "token_name",
          order: "appearance"
        },
        Plot.groupZ(
          {
            y: "sum",
            fill: (d) => (d.token_name === "Other" ? "Other" : d.token_name),
            order: "appearance"
          },
          Plot.groupZ(
            {
              reduce: (group) => {
                const topXGroups = Array.from(group)
                  .sort((a, b) => d3.descending(a[1].usd, b[1].usd))
                  .slice(0, topX)
                  .map(([key]) => key);
                return group.map(([key, value]) => [
                  topXGroups.includes(key) ? key : "Other",
                  value
                ]);
              },
              y: "sum"
            },
            Plot.group(protocol_data, {
              key: (d) => d.token_name,
              value: (d) => ({ usd: +d.usd })
            })
          )
        )
      ),
      Plot.areaY({
        x: "aggregated_date",
        y: "usd",
        fill: "token_name",
        order: "appearance"
      })
    ),
    Plot.ruleY([0])
  ],
  color: {
    legend: true,
    range: d3.schemeTableau10
  },
  x: {
    label: "Date",
    type: "utc",
    grid: true
  },
  y: {
    label: "USD",
    grid: true
  },
  width: 800,
  height: 400
});
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

