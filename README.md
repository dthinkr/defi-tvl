# defi-tvl

## Overview
This project aims to analyze and process data related to Total Value Locked (TVL) in various blockchain protocols. The primary data sources are CoinMetrics and DefiLlama. Initially, the project utilized extracted CSV files but has now transitioned to querying data directly from Google BigQuery.

## Outcomes
- **Data Sources**:
  - CoinMetrics data was found to be insufficiently granular.
  - DefiLlama data could be used with incremental load:
    - The request cap and rate limiting are suitable.
    - The data frequency for TVL and tokens is available in daily and minute intervals.
    
- **ETL for Granular Data**:
  - The ETL process is set up on Google Cloud Services and uses Google BigQuery.
  - The following tables are created:
    - **A**: `protocols`: Contains metadata about each protocol.
    - **B**: `protocol_chain_tvl`: Contains a protocol's TVL separated by chain.
    - **C**: `protocol_token_tvl`: Contains a protocol's TVL separated by token.
    - **D**: `protocol_tvl`: Contains a protocol's aggregated TVL.
  - The relationship among tables B, C, and D is mathematically expressed as follows:
    - At any given time \(t\), the total TVL \(D(t)\) is represented as \(D(t) = \sum\_{i=1}^{n} B\_{\text{chain}\_i}(t) = \sum\_{j=1}^{m} C\_{\text{token}\_j}(t)\), where \(B\_{\text{chain}\_i}(t)\) and \(C\_{\text{token}\_j}(t)\) denote the TVL for the \(i^{th}\) chain in table \(B\) and the \(j^{th}\) token in table \(C\), respectively, and \(n\) and \(m\) are the total number of chains and tokens, respectively.

## How to Use
*Instructions on how to use or access the project can be placed here.*

## Contributing
*Information on contributing to the project can be added here.*

## License
*License information can be included here.*

