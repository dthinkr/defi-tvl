import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.query import BigQueryClient
import pandas_profiling
from streamlit_pandas_profiling import st_profile_report

# Function to retrieve TVL data from table A and C for Aave and Uniswap
def get_tvl_data() -> pd.DataFrame:
    bq_client = BigQueryClient()
    # Retrieve data from table A for Aave and Uniswap
    query_a = """SELECT * FROM `tvl_all.A_protocols` WHERE protocol_name = 'Aave' OR protocol_name = 'Uniswap'"""
    df_a = bq_client.client.query(query_a).to_dataframe()
    # Retrieve data from table C for Aave and Uniswap
    query_c = """SELECT * FROM `tvl_all.C_protocol_token_tvl` WHERE protocol_name = 'Aave' OR protocol_name = 'Uniswap'"""
    df_c = bq_client.client.query(query_c).to_dataframe()
    # Merge the dataframes on the 'protocol_name' column
    merged_df = pd.merge(df_a, df_c, on='protocol_name')
    return merged_df

# Function to plot TVL data
def plot_tvl_data(df: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='date', y='tvl', hue='protocol_name')
    plt.title('TVL of Aave and Uniswap Over Time')
    plt.xlabel('Date')
    plt.ylabel('TVL')
    plt.show()

def generate_profile_report(sample_df):
    """Generate a profile report for a given DataFrame."""
    report = sample_df.profile_report(minimal=True)
    st_profile_report(report)

# Main execution function
def main() -> None:
    # Retrieve TVL data for Aave and Uniswap
    tvl_df = get_tvl_data()
    # Plot the TVL data
    plot_tvl_data(tvl_df)

if __name__ == '__main__':
    main()
    
    