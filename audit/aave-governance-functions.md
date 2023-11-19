# Aave Governance Functions

This document will list all the governance-related function calls within the Aave protocol that can change system parameters.

## Contracts and Functions

The following contracts contain functions that can be called by governance to change system parameters:

- `LendingPoolAddressesProvider.sol`
  - `setLendingPoolImpl(address _pool)`
  - `setLendingPoolCoreImpl(address _lendingPoolCore)`
  - `setLendingPoolConfiguratorImpl(address _configurator)`
  - `setLendingPoolDataProviderImpl(address _provider)`
  - `setLendingPoolParametersProviderImpl(address _parametersProvider)`
  - `setTokenDistributor(address _tokenDistributor)`
  - `setFeeProviderImpl(address _feeProvider)`
  - `setLendingPoolLiquidationManager(address _manager)`
  - `setLendingPoolManager(address _lendingPoolManager)`
  - `setPriceOracle(address _priceOracle)`
  - `setLendingRateOracle(address _lendingRateOracle)`

- `LendingPoolConfigurator.sol`
  - `initReserve(address _reserve, uint8 _underlyingAssetDecimals, address _interestRateStrategyAddress)`
  - `removeLastAddedReserve(address _reserveToRemove)`
  - `enableBorrowingOnReserve(address _reserve, bool _stableBorrowRateEnabled)`
  - `disableBorrowingOnReserve(address _reserve)`
  - `enableReserveAsCollateral(address _reserve, uint256 _baseLTVasCollateral, uint256 _liquidationThreshold, uint256 _liquidationBonus)`
  - `disableReserveAsCollateral(address _reserve)`
  - `enableReserveStableBorrowRate(address _reserve)`
  - `disableReserveStableBorrowRate(address _reserve)`
  - `activateReserve(address _reserve)`
  - `deactivateReserve(address _reserve)`
  - `freezeReserve(address _reserve)`
  - `unfreezeReserve(address _reserve)`
  - `setReserveBaseLTVasCollateral(address _reserve, uint256 _ltv)`
  - `setReserveLiquidationThreshold(address _reserve, uint256 _threshold)`
  - `setReserveLiquidationBonus(address _reserve, uint256 _bonus)`
  - `setReserveDecimals(address _reserve, uint256 _decimals)`
  - `setReserveInterestRateStrategyAddress(address _reserve, address _rateStrategyAddress)`
  - `refreshLendingPoolCoreConfiguration()`

- `DefaultReserveInterestRateStrategy.sol`
  - `baseVariableBorrowRate`
  - `variableRateSlope1`
  - `variableRateSlope2`
  - `stableRateSlope1`
  - `stableRateSlope2`

Please note that this is not an exhaustive list and there may be other functions and contracts within the Aave protocol that allow for governance actions to change system parameters. It is important to review the actual codebase for the most accurate and up-to-date information.