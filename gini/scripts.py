from tqdm import tqdm
from datetime import datetime, timedelta
from web3 import Web3
import pandas as pd
import requests
import math
import time

####

def export_to_multiple_excel(dataframe,  base_filename, chunk_size, folder = None):
    """
    Export a large DataFrame to multiple Excel files.
    
    Args:
    - dataframe (pd.DataFrame): The data to export.
    - base_filename (str): The base name of the output files.
                           Files will be named base_filename_1.xlsx, base_filename_2.xlsx, etc.
    - chunk_size (int): The maximum number of rows per Excel file.
    
    Returns:
    - list of filenames that were created.
    """

    # Split the dataframe into chunks
    chunks = [dataframe.iloc[i:i+chunk_size] for i in range(0, len(dataframe), chunk_size)]
    
    filenames = []

    for i, chunk in enumerate(chunks, 1):
        filename = f"{base_filename}_{i}.xlsx"
        if folder:
            chunk.to_excel(folder+filename, index=False)
        else:
            chunk.to_excel(filename, index=False)
        filenames.append(filename)
        print(f"Saved {filename}")

    return filenames

def etherscan_to_dataframe(etherscan_response):
    output = pd.DataFrame(etherscan_response.json()['result'])
    return output


def data_query(token_address, last_date, api_key):
    start_block = 0
    end_block = 99999999999
    storage = []
    dt = datetime.strptime(last_date, '%Y-%m-%d')
    current_time = 0
    
    with tqdm(total=int(dt.timestamp())) as pbar:  # Create progress bar
        while current_time < int(dt.timestamp()):
            url = f'http://api.etherscan.io/api?module=account&action=tokentx&' \
                  f'contractaddress={token_address}&' \
                  f'startblock={start_block}&endblock={end_block}&sort=asc&apikey={api_key}'
            response = requests.get(url)
            print(response.status_code)
            if response.status_code== 200:
                print(url)
                
                tempt_output = pd.DataFrame(response.json()['result'])
                storage.append(tempt_output)
                start_block = int(tempt_output['blockNumber'].astype(float).max())
                new_time = int(tempt_output['timeStamp'].max())  # Get the new time first
            
                # Update progress bar by the difference between new time and old time
                pbar.update(new_time - current_time)
                current_time = new_time
            
                #storage.append(tempt_output)
            else:
                time.sleep(3)
            
            time.sleep(3)
    output = pd.concat(storage)
    return output

####

def current_price_query(asset_id):
    coingecko_api = 'CG-PvXVa7KUKKi5TwFzYpG3DevQ'
    coingecko_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={asset_id}&x_cg_demo_api_key={coingecko_api}"
    response = requests.get(coingecko_url).json()
    try:
        price = response[0]['current_price']
        return price
    except IndexError:
        print("Please provide a valid asset id in CoinGecko")

def circulating_supply_query(asset_id):
    coingecko_api = 'CG-PvXVa7KUKKi5TwFzYpG3DevQ'
    coingecko_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={asset_id}&x_cg_demo_api_key={coingecko_api}"
    response = requests.get(coingecko_url).json()
    try:
        total_supply = response[0]['circulating_supply']
        return total_supply
    except IndexError:
        print("Please provide a valid asset id in CoinGecko")

def total_supply_query(asset_id):
    coingecko_api = 'CG-PvXVa7KUKKi5TwFzYpG3DevQ'
    coingecko_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={asset_id}&x_cg_demo_api_key={coingecko_api}"
    response = requests.get(coingecko_url).json()
    try:
        total_supply = response[0]['total_supply']
        return total_supply
    except IndexError:
        print("Please provide a valid asset id in CoinGecko")

def ratio_measures(holder_list, ratio='90/10'):
    # Sort the balance sheet and reset index
    holder_list = holder_list.sort_values('balance')
    holder_list = holder_list.reset_index(drop = True)
    
    # Calculate top N% people's total wealth
    total_holders = holder_list.shape[0]
    percentage_breakdown = ratio.split('/')
    top_start_index = math.floor(total_holders * (float(percentage_breakdown[0])/100))
    top_wealth = holder_list.loc[top_start_index:,'balance'].sum()
    
    # Calculate botton N% people's total wealth
    bottom_end_index = math.floor(total_holders * (float(percentage_breakdown[1])/100))
    bottom_wealth = holder_list.loc[0:bottom_end_index,'balance'].sum()
    
    return round(top_wealth/bottom_wealth,2)
    
def pyramid_chart_table(df, date, bins, labels, token_decimal = 0, ratio = '90/10',mode = 'token', asset_id = None):
    #df is the output dataframe from balance_check() function
    holder_list = holders_uptil_date(df,date)
    holder_list['token'] = (holder_list['balance']/(10**token_decimal)).astype(float)
    holder_list = holder_list.sort_values('token',ascending = True)
    
    
    
    if mode == 'wealth':
        # Query current asset price and calculate value in each address
        assert asset_id is not None, "Please provide a valid asset id"
        asset_price = current_price_query(asset_id)
        holder_list['wealth'] = holder_list['token'] * asset_price
        
        # Categorize the amounts into bins
        holder_list['category'] = pd.cut(holder_list['wealth'], bins=bins, labels=labels, right=False)
    
        # Calculate the total supply of token and total number of holders
        total_supply =  total_supply_query(asset_id)
        circulating_supply =  total_supply_query(asset_id)
        total_holder = holder_list['address'].count()
    
        # Calculate total token held and the number of holders in each group
        grouped = holder_list.groupby('category')['wealth'].agg(['count', 'sum'])
        grouped.columns = ['Number of holders', 'Total wealth held in USD']
        
        # Calculate the percentage of total token held and the number of holders in each group
        grouped['Wealth held percentage'] = (grouped['Total wealth held in USD'] / (grouped['Total wealth held in USD'].sum())) * 100
        grouped['Holder percentage'] = (grouped['Number of holders'] / total_holder) * 100
        grouped.reset_index(drop = False,inplace = True)
        grouped['Total wealth held in USD'] = round(grouped['Total wealth held in USD'],2).astype(str)
        
        print(f'The current price for {asset_id} is ${asset_price}.')
        print(f'There are {total_holder} holders in {asset_id}.')
        print(f'The total value of {asset_id} is ${round(circulating_supply*asset_price,2)}.')
        print(f'The average value held by each person is ${round(total_supply*asset_price/total_holder,2)}.')
        inequality_ratio = ratio_measures(holder_list, ratio=ratio)
        print(f'The {ratio} ratio meansure for {asset_id} is {inequality_ratio}.')
    
    
        return grouped
    
        
    elif mode == 'token':
        # Categorize the amounts into bins
        holder_list['category'] = pd.cut(holder_list['token'], bins=bins, labels=labels, right=False)
    
        # Calculate the total supply of token and total number of holders
        total_supply = holder_list['token'].sum()
        total_holder = holder_list['address'].count()
    
        # Calculate total token held and the number of holders in each group
        grouped = holder_list.groupby('category')['token'].agg(['count', 'sum'])
        grouped.columns = ['Number of holders', 'Total token held']

        # Calculate the percentage of total token held and the number of holders in each group
        grouped['Token held percentage'] = (grouped['Total token held'] / total_supply) * 100
        grouped['Holder percentage'] = (grouped['Number of holders'] / total_holder) * 100
        grouped.reset_index(drop = False,inplace = True)
    
    
        return grouped
    
def token_to_usd(ledger,token_col,token_id,token_decimal=18):
    price = current_price_query(asset_id = token_id)
    total_supply = total_supply_query(asset_id = token_id)
    ledger[token_col+'_usd'] = round((ledger[token_col].astype(float)/(10**token_decimal)) * price,2)
    total_usd = price * total_supply
    ledger[token_col+'_usd'] = ledger[token_col+'_usd'].astype(str)
    ledger[token_col+'_pct'] = round((ledger[token_col+'_usd'].astype(float)/ total_usd) *100,2).astype(str) +'%'
    selected_address_pct = round((ledger[token_col+'_usd'].astype(float)/ total_usd) *100,2).sum()
    print(f"Top {ledger.shape[0]} addresses cover {round(selected_address_pct,2)}% of total value in {token_id}.")
    return ledger 

####

def unix_timestamp_to_date(timestamp):
    """Convert Unix timestamp to a date in yyyy-mm-dd format."""
    # Ensure timestamp is an integer
    timestamp = int(timestamp)
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def balance_tracker(df,time_col, address_from_col, address_to_col,value,excluded_address):
    exclude_address_list = [x.lower() for x in excluded_address]
    #exclude transactions that involved governance contract (other excluded addresses)
    data = df[[x not in exclude_address_list for x in df[address_from_col]]]
    data = data[[x not in exclude_address_list for x in data[address_to_col]]]
    
    #aggregate all the transactions out and in
    outcoming = data.groupby([time_col,address_from_col],as_index = False)[value].sum()
    incoming = data.groupby([time_col,address_to_col],as_index = False)[value].sum()
    
    outcoming.rename({value:'outcome value',
                      address_from_col:'address'},axis = 1,inplace = True)
    incoming.rename({value:'income value',
                    address_to_col:'address'},axis = 1,inplace = True)
    
    output = pd.merge(outcoming,incoming, how = 'outer', on = [time_col,'address'])
    output = output.fillna(0)
    
    output['balance'] = output['income value'] -output['outcome value']
    output = output.sort_values([time_col,'balance'])
    return output

def holders_uptil_date(df, given_date):
    # Filter the dataframe based on the given date
    filtered_df = df[df['date'] <= given_date]
    
    # Group by address and sum the balance
    aggregated_df = filtered_df.groupby('address').agg({'balance': 'sum'}).reset_index()
    aggregated_df.sort_values('balance',ascending = True,inplace = True)
    aggregated_df = aggregated_df.reset_index(drop = True)
    
    # filter out contract with negative balances
    aggregated_df = aggregated_df[aggregated_df['balance']>0]
    return aggregated_df

def ledger_to_balances(transaction_df, excluded_contracts, traceback_contracts, top=20):
    # track balance without excluding and traceback any contract
    empty_address = []
    output_transaction_df = balance_tracker(transaction_df,'date', 'address_from', 'address_to','value',empty_address)
    address_book = holders_uptil_date(output_transaction_df,'2023-12-01').tail(top)['address'].to_list()

    # based on current N holders, exclude the contract
    contract_query = check_contract(address_book)
    query_results = pd.DataFrame(contract_query.items(),columns = ['address','address_type'])
    contract_to_exclude = query_results[query_results['address_type'] == 'contract']
    contract_to_exclude = contract_to_exclude['address'].to_list()

    # compile exclude contract list and traceback contract list
    traceback_contract = traceback_contracts

    contract_to_exclude_additional = excluded_contracts
    
    contract_to_exclude_additional = [x.lower() for x in contract_to_exclude_additional]

    contract_to_exclude.extend(contract_to_exclude_additional)

    print(f'The following is contract to traceback:')
    for x in traceback_contract:
        print(f'{x},')

    print('\n\n')
    print(f'The following is contract to exclude:')
    for x in contract_to_exclude:
        print(f'{x},')


    # track balance again with traceback contract
    output_transaction_df = balance_tracker(transaction_df,'date', 'address_from', 'address_to','value',traceback_contract)
    output_transaction_df = output_transaction_df[[x not in contract_to_exclude for x in output_transaction_df['address']]]
    
    return output_transaction_df, contract_to_exclude

def check_contract(address_book):
    result = {}
    infura_url = "https://mainnet.infura.io/v3/45d53142aa6444c08ea4baacf4bd41f4"
    web3 = Web3(Web3.HTTPProvider(infura_url))
    for address in address_book:
        result[address] = None
        checksum_address = Web3.to_checksum_address(address)
        response = web3.eth.get_code(checksum_address)
        if response.hex() == '0x':
            result[address] = 'address'
        else:
            result[address] = 'contract'
    return result



####


def gini_coefficient(data):
    """
    Calculate Gini coefficient using relative mean absolute difference.

    Parameters:
    - data (list): List of values for which Gini coefficient is to be computed.

    Returns:
    - float: Gini coefficient.
    """

    n = len(data)
    sum_diffs = sum(abs(x - y) for i, x in enumerate(data) for j, y in enumerate(data))
    sum_vals = sum(data)
    gini = sum_diffs / (2 * n * sum_vals)
    
    return gini

def gini_coefficient_quick(data):
    ## data should be a sorted dataay
    n = data.size
    coef_ = 2. / n
    const_ = (n + 1.) / n
    weighted_sum = sum([(i+1)*yi for i, yi in enumerate(data)])
    return coef_*weighted_sum/(data.sum()) - const_

def calculate_gini(data, date_col, start_date = None):
    
    if not start_date:
        start_date = str(pd.to_datetime(data[date_col]).min().date())
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Calculate the number of days for the progress bar
    total_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1

    results = []

    # Loop through each day from start_date to end_date with a progress bar
    for _ in tqdm(range(total_days), desc="Processing"):
        holders = holders_uptil_date(data, start_date)
        gini_value = gini_coefficient_quick(holders['balance'].astype(float).values)
        
        # Append the result to the results list
        results.append({
            'date': start_date,
            'gini_coefficient': gini_value
        })

        # Move to the next day
        datetime_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        datetime_start_date += timedelta(days=1)
        start_date = datetime_start_date.strftime("%Y-%m-%d")

    # Convert the results list to a DataFrame
    result_df = pd.DataFrame(results)
    return result_df



####

def export_to_multiple_excel(dataframe,  base_filename, chunk_size, folder = None):
    """
    Export a large DataFrame to multiple Excel files.
    
    Args:
    - dataframe (pd.DataFrame): The data to export.
    - base_filename (str): The base name of the output files.
                           Files will be named base_filename_1.xlsx, base_filename_2.xlsx, etc.
    - chunk_size (int): The maximum number of rows per Excel file.
    
    Returns:
    - list of filenames that were created.
    """

    # Split the dataframe into chunks
    chunks = [dataframe.iloc[i:i+chunk_size] for i in range(0, len(dataframe), chunk_size)]
    
    filenames = []

    for i, chunk in enumerate(chunks, 1):
        filename = f"{base_filename}_{i}.xlsx"
        if folder:
            chunk.to_excel(folder+filename, index=False)
        else:
            chunk.to_excel(filename, index=False)
        filenames.append(filename)
        print(f"Saved {filename}")

    return filenames

def etherscan_to_dataframe(etherscan_response):
    output = pd.DataFrame(etherscan_response.json()['result'])
    return output


def data_query(token_address, last_date, api_key):
    start_block = 0
    end_block = 99999999999
    storage = []
    dt = datetime.strptime(last_date, '%Y-%m-%d')
    current_time = 0
    
    with tqdm(total=int(dt.timestamp())) as pbar:  # Create progress bar
        while current_time < int(dt.timestamp()):
            url = f'http://api.etherscan.io/api?module=account&action=tokentx&' \
                  f'contractaddress={token_address}&' \
                  f'startblock={start_block}&endblock={end_block}&sort=asc&apikey={api_key}'
            response = requests.get(url)
            print(response.status_code)
            if response.status_code== 200:
                print(url)
                
                tempt_output = pd.DataFrame(response.json()['result'])
                storage.append(tempt_output)
                start_block = int(tempt_output['blockNumber'].astype(float).max())
                new_time = int(tempt_output['timeStamp'].max())  # Get the new time first
            
                # Update progress bar by the difference between new time and old time
                pbar.update(new_time - current_time)
                current_time = new_time
            
                #storage.append(tempt_output)
            else:
                time.sleep(3)
            
            time.sleep(3)
    output = pd.concat(storage)
    return output


####

def get_coingecko_coin_ids():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    coins = response.json()
    # Convert coin names to lower case for case-insensitive matching
    return {coin['name'].lower(): coin['id'] for coin in coins}