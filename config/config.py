# config.py
# DATA_DIR = "../data/"
# json_files_dir = DATA_DIR + "tvl/"
# protocol_headers_path = DATA_DIR + "headers/protocol_headers.json"

TOP_N = 8

CACHE_DIR = "data/tvl/cache/"

QUERY_PROJECT = "platinum-analog-402701"

QUERY_DATA_SET = "tvl_all"

TABLES = {
    "A": "A_protocols",
    "B": "B_protocol_chain_tvl",
    "C": "C_protocol_token_tvl",
    "D": "D_protocol_tvl",
    "E": "E_chain_ndc_tvl",
}

CATEGORY_MAPPING = {
    "Asset Management": [
        "Algo-Stables",
        "Decentralized Stablecoin",
        "Liquid Staking",
        "Liquidity manager",
        "Reserve Currency",
        "Synthetics",
        "Yield",
        "Yield Aggregator",
    ],
    "Trading & Exchanges": [
        "Bridge",
        "CEX",
        "Cross Chain",
        "Dexes",
        "Derivatives",
        "Options",
        "Options Vault",
        "NFT Marketplace",
    ],
    "Lending, Borrowing & Real World Assets": [
        "CDP",
        "Lending",
        "Leveraged Farming",
        "NFT Lending",
        "RWA Lending",
        "Uncollateralized Lending",
        "RWA",
    ],
    "Infrastructure, Services & Financial Products": [
        "Chain",
        "Infrastructure",
        "Oracle",
        "Payments",
        "Services",
        "Farm",
        "Gaming",
        "Indexes",
        "Insurance",
        "Launchpad",
        "Prediction Market",
        "Staking Pool",
    ],
    "Privacy & Security": ["Privacy"],
    "Others": ["SoFi"],
}


original_names = [
    "Trading & Exchanges",
    "Lending, Borrowing & Real World Assets",
    "Asset Management",
    "Infrastructure, Services & Financial Products",
    "Privacy & Security",
    "Others"
]

# Creating abbreviations for the original names
abbreviated_names = [
    "Trade/Exch",                   # Abbreviation for "Trading & Exchanges"
    "Lend/Borrow/RWA",              # Abbreviation for "Lending, Borrowing & Real World Assets"
    "Asset Mgmt",                   # Abbreviation for "Asset Management"
    "Infra/Serv/FinProd",           # Abbreviation for "Infrastructure, Services & Financial Products"
    "Privacy/Sec",                  # Abbreviation for "Privacy & Security"
    "Others"                        # Abbreviation remains the same for "Others"
]

# Creating a Python dictionary with the provided token to protocol/entity mapping

PRIMARY_TOKEN_TO_PROTOCOL = {
    "USDC": "Circle",
    "USDT": "Tether",
    "WETH": "Ethereum",
    "DAI": "MakerDAO",
    "WBTC": "BitGo",
    "ETH": "Ethereum",
    "BUSD": "Binance",
    "WBNB": "Binance",
    "USDC.E": "Circle",
    "BNB": "Binance",
    "POLYGONUSDC": "Circle",
    "WMATIC": "Polygon",
    "BTCB": "Binance",
    "FTM": "Fantom",
    "WAVAX": "Avalanche",
    "WFTM": "Fantom",
    "FRAX": "Frax Finance",
    "MIM": "Abracadabra.money",
    "TUSD": "TrustToken",
    "UST": "Terra",
    "USDT.E": "Tether",
    "DAI.E": "MakerDAO",
    "FUSDT": "Tether",
    "WETH.E": "Ethereum",
    "DOT": "Polkadot",
    "ADA": "Cardano",
    "MIMATIC": "Abracadabra.money",
    "AVALANCHEUSDC": "Circle",
    "WSTETH": "Lido",
    "OP": "Optimism",
    "XRP": "Ripple",
    "SUSD": "Synthetix",
    "RETH": "Rocket Pool",
    "USTC": "Terra",
    "DOGE": "Dogecoin",
    "LUSD": "Liquity",
    "WBTC.E": "BitGo",
    "HBTC": "Huobi",
    "RENBTC": "Ren",
    "MANA": "Decentraland",
    "MAI": "Qi Dao",
    "STETH": "Lido",
    "GRT": "The Graph",
    "LTC": "Litecoin",
    "LUNC": "Terra",
    "TRX": "TRON",
    "LUNA": "Terra",
    "STMATIC": "Polygon",
    "ATOM": "Cosmos",
    "AXS": "Axie Infinity",
    "FEI": "Fei Protocol",
    "USDBC": "Unknown",
    "AGEUR": "Angle",
    "DPI": "Index Coop",
    "BTC.B": "Unknown",
    "METIS": "Metis",
    "GOHM": "Olympus",
    "USDP": "Paxos",
    "RAI": "Reflexer",
    "HUSD": "Huobi",
    "PAXG": "Paxos",
    "AXLUSDC": "Circle",
    "MATICX": "Polygon",
    "HT": "Huobi",
    "ENJ": "Enjin",
    "FIL": "Filecoin",
    "BTCBR": "BitcoinBR",
    "WXDAI": "Gnosis",
    "3CRV": "Curve",
    "POLYDOGE": "PolyDoge",
    "WMEMO": "Wonderland",
    "CEL": "Celsius",
    "EURS": "STASIS",
    "BCH": "Bitcoin Cash",
    "AMUSDC": "Aave",
    "USD+": "Overnight USD+",
    "CUSD": "Celo",
    "WONE": "Harmony",
    "LINK.E": "Chainlink",
    "WCRO": "Crypto.com",
    "JEUR": "STASIS",
    "GALA": "Gala Games",
    "WGLMR": "Moonbeam",
    "AMDAI": "Aave",
    "OCEAN": "Ocean Protocol",
    "DOLA": "Dollar Protocol",
    "BAND": "Band Protocol",
    "1USDC": "Circle",
    "CDAI": "Compound",
    "NEAR": "NEAR Protocol",
    "TWT": "Trust Wallet",
    "ALUSD": "Alchemix",
    "WSOL": "Solana",
    "BOB": "Explain This Bob",
    "WUSDR": "Tangible",
    "JPYC": "JPY Coin",
    "ANY": "Anyswap",
    "1ETH": "Ethereum",
    "SETH": "Synthetix",
    "UMA": "UMA Protocol"
}