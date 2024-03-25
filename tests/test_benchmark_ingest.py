import pandas as pd
import polars as pl
import time
import pytest

def generate_pandas_dataframe(size):
    date_unix_timestamp = int(time.mktime(time.strptime("2021-01-01", "%Y-%m-%d")))
    data = {
        "id": list(range(size)),
        "chain_name": ["chain_" + str(i % 10) for i in range(size)],
        "date": [date_unix_timestamp for _ in range(size)],
        "token_name": ["token_" + str(i % 5) for i in range(size)],
        "quantity": list(range(size)),
        "value_usd": list(range(size)),
    }
    df = pd.DataFrame(data)
    return df

def benchmark_pandas(df):
    start_time = time.time()
    filtered_df = df[df["id"] > 5000]
    end_time = time.time()
    return end_time - start_time

def benchmark_polars(df):
    pl_df = pl.from_pandas(df)
    start_time = time.time()
    filtered_df = pl_df.filter(pl.col("id") > 5000)
    end_time = time.time()
    return end_time - start_time

@pytest.mark.parametrize("size", [10000, 100000, 1000000, 10000000])
def test_performance_comparison(size, capsys):
    df = generate_pandas_dataframe(size)
    pandas_time = benchmark_pandas(df)
    polars_time = benchmark_polars(df)
    
    if pandas_time > polars_time:
        speedup = pandas_time / polars_time
        result_message = f"\nSize: {size}, Polars is {speedup:.2f}x faster than Pandas."
    elif polars_time > pandas_time:
        speedup = polars_time / pandas_time
        result_message = f"\nSize: {size}, Pandas is {speedup:.2f}x faster than Polars."
    else:
        result_message = f"\nSize: {size}, Polars and Pandas have similar performance."
    
    print(result_message)
    # Use capsys to read captured output and then print it, effectively bypassing pytest's output capture
    captured = capsys.readouterr()
    print(captured.out)