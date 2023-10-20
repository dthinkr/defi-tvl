# config.py
DATA_DIR = "../data/"

category_mapping = {
    "Asset Management": [
        "Algo-Stables",
        "Decentralized Stablecoin",
        "Liquid Staking",
        "Liquidity manager",
        "Reserve Currency",
        "Synthetics",
        "Yield",
        "Yield Aggregator"
    ],
    "Trading & Exchanges": [
        "Bridge",
        "CEX",
        "Cross Chain",
        "Dexes",
        "Derivatives",
        "Options",
        "Options Vault",
        "NFT Marketplace"
    ],
    "Lending, Borrowing & Real World Assets": [
        "CDP",
        "Lending",
        "Leveraged Farming",
        "NFT Lending",
        "RWA Lending",
        "Uncollateralized Lending",
        "RWA"
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
        "Staking Pool"
    ],
    "Privacy & Security": ["Privacy"],
    "Others": ["SoFi"]
}

json_files_dir = DATA_DIR + "tvl/"

protocol_headers_path = DATA_DIR + "headers/protocol_headers.json"