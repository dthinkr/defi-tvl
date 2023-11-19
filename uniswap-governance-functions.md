# Uniswap Governance Functions

This document will list all the governance-related function calls within the Uniswap protocol that can change system parameters.

## Contracts and Functions

The following contracts contain functions that can be called by governance to change system parameters:

- `IUniswapV3Factory.sol`
  - `OwnerChanged(address indexed oldOwner, address indexed newOwner)`

- `UniswapV3Factory.sol`
  - `owner`
  - `feeAmountTickSpacing`
  - `getPool`

- `UniswapV3Pool.sol`
  - `factory`
  - `token0`
  - `token1`
  - `fee`
  - `tickSpacing`

- `UniswapV3PoolDeployer.sol`
  - `parameters`

Please note that this is not an exhaustive list and there may be other functions and contracts within the Uniswap protocol that allow for governance actions to change system parameters. It is important to review the actual codebase for the most accurate and up-to-date information.