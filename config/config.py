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