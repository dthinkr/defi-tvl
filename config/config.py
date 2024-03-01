# config.py
# DATA_DIR = "../data/"
# protocol_headers_path = DATA_DIR + "headers/protocol_headers.json"

TOP_N = 8

CACHE_DIR = "data/tvl/cache/"

MAPPING_PATH = 'data/mapping/'

QUERY_PROJECT = "platinum-analog-402701"

QUERY_DATA_SET = "tvl_all"

SIMILARIY_THRESHOLD = 0.2

CUSTOM_COLORS = ["#ecdab0", "#e9c8b1", "#dbb1c3", 
                 "#b5bbe7", "#b6cfce", "#d8d9dd"]

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

NETWORK_PRELIMINARIES = """
                        ### Preliminaries

                        Let:

                        - $\mathcal{A}$ represent the set of all protocols, where each protocol $a \in \mathcal{A}$ is identified by a unique identifier $id_a$, and may have associated attributes such as name and URL.
                        - $\mathcal{C}$ denote the set of time-based data entries, where each entry $c \in \mathcal{C}$ corresponds to a token and includes information on the token's name, the change in its locked value over a specified time interval, and possibly its association with a protocol in $\mathcal{A}$.

                        ### Categorization Function

                        Define a categorization function $\phi: \mathcal{C} \\rightarrow \mathcal{K}$, which maps each token $c$ to a category $k \in \mathcal{K} = \{ rev\_map, LP, UNKNOWN, Other \}$ based on predefined rules related to the token's name and presence in reverse mappings or lists.

                        ### Processing Functions

                        1. **Unknown Tokens Processing** $\psi_{UNKNOWN}: \mathcal{C}_{UNKNOWN} \\rightarrow \mathcal{A}$: For tokens categorized as UNKNOWN, this function attempts to match token names to Ethereum addresses and subsequently to protocol identifiers in $\mathcal{A}$, effectively refining $\mathcal{C}_{UNKNOWN}$ to a more identifiable subset of $\mathcal{A}$.

                        2. **Other Tokens Processing** $\psi_{Other}: \mathcal{C}_{Other} \\rightarrow \mathcal{A} \cup \{ null \}$: Applies manual mappings and filters to tokens in the Other category, potentially mapping them to protocols in $\mathcal{A}$ or excluding them (mapped to null).

                        3. **Reverse Mapping Application** $\psi_{rev\_map}: \mathcal{C}_{rev\_map} \\rightarrow \mathcal{A}$: Directly maps tokens in the rev_map category to protocols in $\mathcal{A}$ using the provided reverse mapping.

                        ### Merging and Sorting

                        After processing, the subsets of $\mathcal{C}$ are merged into a single set $\mathcal{C}_{merged}$, which is then sorted based on the magnitude of value change, resulting in $\mathcal{C}_{sorted}$.

                        ### Graph Construction

                        Construct a directed graph $G = (V, E)$ where:

                        - $V$ corresponds to protocols in $\mathcal{A}$, with each node $v$ representing a protocol.
                        - $E$ consists of directed edges between nodes in $V$, with each edge $e(v_i, v_j)$ representing the flow of value from protocol $v_i$ to protocol $v_j$, derived from $\mathcal{C}_{sorted}$. The weight of each edge is proportional to the magnitude of the value change.

                        """