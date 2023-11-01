# defi-tvl

## Overview
This project aims to analyze and process data related to Total Value Locked (TVL) in various blockchain protocols. The primary data sources are CoinMetrics and DefiLlama. The project has evolved from utilizing extracted CSV files to directly querying data from Google BigQuery for a more efficient and streamlined analysis.

## Outcomes
- **Data Sources**:
  - **CoinMetrics**: The data from CoinMetrics was found to lack granularity, making it less suitable for detailed analysis.
  - **DefiLlama**: DefiLlama data proved to be a valuable resource:
    - Request cap and rate limiting are well-suited for this project's needs.
    - Data frequency for TVL and tokens is available in both daily and minute intervals.
    
- **ETL for Granular Data**:
  - The ETL (Extract, Transform, Load) process is established using Google Cloud Services and Google BigQuery.
  - The data is organized into the following tables:
    - $A$: `protocols`: This table contains metadata for each protocol.
    - $B$: `protocol_chain_tvl`: This table details a protocol's TVL, separated by chain.
    - $C$: `protocol_token_tvl`: This table details a protocol's TVL, separated by token.
    - $D$: `protocol_tvl`: This table aggregates a protocol's TVL.

- **Table Relations**
  - Each table is a set $A, B, C, D$.
  - $\mathbf{z}$: A set of all protocols, where $\mathbf{z} = (z_1, z_2, \dots, z_k)$.
  - $\mathbf{x}$: A set of all chains related to a protocol, where $\mathbf{x} = (x_1, x_2, \dots, x_n)$.
  - $\mathbf{y}$: A set of all tokens associated with a protocol, where $\mathbf{y} = (y_1, y_2, \dots, y_m)$.
  - $B_{z_i}(t)$: A function representing the TVL for the $i^{th}$ protocol in table $B$ separated by chain at time $t$.
  - $C_{z_i}(t)$: A function representing the TVL for the $i^{th}$ protocol in table $C$ separated by token at time $t$.
  - $D_{z_i}(t)$: A function representing the total aggregated TVL for the $i^{th}$ protocol at time $t$.
  - At any given time $t$, the total TVL $D_{z_i}(t)$ for a protocol $z_i$ satisfies:
    - $D_{z_i}(t) = \sum_{j=1}^{n} B_{z_i, x_j}(t) = \sum_{k=1}^{m} C_{z_i, y_k}(t)$
    - Here, $n$ and $m$ represent the total number of chains and tokens associated with $z_i$.

## How to Use
To use this project, you can clone the repository to your local machine or development environment. Ensure that you have the necessary credentials and access to Google BigQuery. You can then run the scripts provided to extract and analyze the TVL data as per your needs.

## Contributing
Contributions to enhance this project are welcome. Feel free to open an issue or create a pull request.

## License
Please refer to the `LICENSE` file in the repository for information regarding licensing.
