import yfinance as yf
import pandas as pd
import time

# Function to fetch historical stock data
def getCandlestickChartData(ticker: str) -> pd.DataFrame:
    # Download stock data using Yahoo Finance API
    df = yf.download(ticker, multi_level_index=False, auto_adjust=False)
    
    # Return the data (with most recent dates first)
    return df.sort_index(ascending=False)