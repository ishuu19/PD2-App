"""Stock Data Service with yfinance - 5+ Years Historical Data"""
import yfinance as yf
import pandas as pd
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import streamlit as st
import database.models as db
from config import constants
import os

# Create cache directory for storing data
if not os.path.exists('.yfinance_cache'):
    os.makedirs('.yfinance_cache')

def _load_stock_from_csv(ticker: str) -> Optional[pd.DataFrame]:
    """Load stock data from CSV file"""
    csv_path = f"data/{ticker}_daily.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            # Rename columns to lowercase
            df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
            return df
        except Exception as e:
            print(f"Error loading {ticker} from CSV: {e}")
    return None

def _download_top_stocks_data():
    """Download 5+ years of historical data for top 20 stocks using yfinance"""
    tickers = constants.HK_STOCKS
    stocks_data = {}
    
    try:
        print(f"Loading data for {len(tickers)} stocks from CSV files...")
        
        # Try to load from CSV first, then download if needed
        for i, ticker in enumerate(tickers):
            try:
                print(f"Loading {ticker} ({i+1}/{len(tickers)})...")
                
                # Try CSV first
                df = _load_stock_from_csv(ticker)
                
                # If CSV doesn't exist or is empty, download from yfinance
                if df is None or df.empty:
                    print(f"  CSV not found, downloading {ticker}...")
                    ticker_obj = yf.Ticker(ticker)
                    df = ticker_obj.history(period="6y", interval="1d")
                
                if df.empty:
                    print(f"  No data for {ticker}")
                    continue
                
                # Process the data (columns should already be lowercase from CSV loading)
                if not all(col.lower() == col for col in df.columns):
                    # Rename columns to lowercase if not already
                    df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
                
                # Get stock name
                stock_name = constants.STOCK_NAMES.get(ticker, ticker)
                
                # Calculate metrics
                current_price = df['close'].iloc[-1] if 'close' in df.columns else df.iloc[:, 0].iloc[-1]
                prev_close = df['close'].iloc[-2] if len(df) > 1 and 'close' in df.columns else current_price
                change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                # Calculate historical returns
                returns_1m = df['close'].pct_change(20).iloc[-1] * 100 if len(df) > 20 and 'close' in df.columns else 0
                returns_3m = df['close'].pct_change(60).iloc[-1] * 100 if len(df) > 60 and 'close' in df.columns else 0
                returns_6m = df['close'].pct_change(120).iloc[-1] * 100 if len(df) > 120 and 'close' in df.columns else 0
                returns_1y = df['close'].pct_change(252).iloc[-1] * 100 if len(df) > 252 and 'close' in df.columns else 0
                
                # Volatility (annualized)
                volatility = df['close'].pct_change().std() * (252 ** 0.5) * 100 if 'close' in df.columns else 0
                
                # 52-week high/low
                high_52w = df['high'].tail(252).max() if len(df) >= 252 and 'high' in df.columns else df['high'].max() if 'high' in df.columns else current_price
                low_52w = df['low'].tail(252).min() if len(df) >= 252 and 'low' in df.columns else df['low'].min() if 'low' in df.columns else current_price
                
                # Handle NaN values safely
                volume_value = df['volume'].iloc[-1] if 'volume' in df.columns else 0
                volume_int = int(volume_value) if pd.notna(volume_value) else 0
                
                hist_data = df[['open', 'high', 'low', 'close', 'volume']].tail(252) if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']) else df.iloc[:, :5].tail(252)
                
                stocks_data[ticker] = {
                    'ticker': ticker,
                    'name': stock_name,
                    'current_price': current_price,
                    'previous_close': prev_close,
                    'change_percent': round(change_pct, 2) if pd.notna(change_pct) else 0,
                    'volume': volume_int,
                    'market_cap': 0,
                    'pe_ratio': 0,
                    'dividend_yield': 0,
                    'beta': 1.0,
                    'volatility': round(volatility, 2) if pd.notna(volatility) else 0,
                    'high_52w': high_52w,
                    'low_52w': low_52w,
                    'returns_1m': round(returns_1m, 2) if pd.notna(returns_1m) else 0,
                    'returns_3m': round(returns_3m, 2) if pd.notna(returns_3m) else 0,
                    'returns_6m': round(returns_6m, 2) if pd.notna(returns_6m) else 0,
                    'returns_1y': round(returns_1y, 2) if pd.notna(returns_1y) else 0,
                    'historical': hist_data,
                    'sector': 'Unknown',
                    'industry': 'Unknown',
                    'last_updated': datetime.now()
                }
                print(f"  ✓ {ticker}: ${current_price:.2f}")
            except Exception as e:
                print(f"  ✗ Failed to download {ticker}: {str(e)}")
                continue
        
        print(f"\nSuccessfully processed {len(stocks_data)} stocks from yfinance")
        return stocks_data
        
    except Exception as e:
        print(f"Error downloading stock data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def _should_refresh_data():
    """Check if data should be refreshed (after midnight or first load)"""
    if 'last_refresh_time' not in st.session_state:
        return True
    
    last_refresh = st.session_state.last_refresh_time
    now = datetime.now()
    
    # Refresh if it's been more than 6 hours (market is open)
    time_diff = now - last_refresh
    if time_diff.total_seconds() > 6 * 3600:  # 6 hours in seconds
        return True
    
    return False

def _initialize_stock_data():
    """Initialize stock data on first load"""
    if 'top_stocks_data' not in st.session_state or _should_refresh_data():
        # Don't show spinner here - let the caller control it
        st.session_state.top_stocks_data = _download_top_stocks_data()
        st.session_state.last_refresh_time = datetime.now()

def _fetch_single_stock_yfinance(ticker: str) -> Optional[Dict]:
    """Fetch data for a single stock using yfinance"""
    try:
        # Use individual ticker download for stocks not in top 20
        data = yf.download(
            ticker,
            start="2018-01-01",
            end=None,
            interval='1d',
            progress=False,
            threads=True
        )
        
        if data.empty:
            return None
            
        df = data.copy()
        
        # Rename columns to lowercase
        df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
        
        # Get stock name
        stock_name = constants.STOCK_NAMES.get(ticker, ticker)
        
        # Calculate metrics
        current_price = df['close'].iloc[-1] if 'close' in df.columns else df.iloc[:, 0].iloc[-1]
        prev_close = df['close'].iloc[-2] if len(df) > 1 and 'close' in df.columns else current_price
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        # Calculate historical returns
        returns_1m = df['close'].pct_change(20).iloc[-1] * 100 if len(df) > 20 and 'close' in df.columns else 0
        returns_3m = df['close'].pct_change(60).iloc[-1] * 100 if len(df) > 60 and 'close' in df.columns else 0
        returns_6m = df['close'].pct_change(120).iloc[-1] * 100 if len(df) > 120 and 'close' in df.columns else 0
        returns_1y = df['close'].pct_change(252).iloc[-1] * 100 if len(df) > 252 and 'close' in df.columns else 0
        
        # Volatility (annualized)
        volatility = df['close'].pct_change().std() * (252 ** 0.5) * 100 if 'close' in df.columns else 0
        
        # 52-week high/low
        high_52w = df['high'].tail(252).max() if len(df) >= 252 and 'high' in df.columns else df['high'].max() if 'high' in df.columns else current_price
        low_52w = df['low'].tail(252).min() if len(df) >= 252 and 'low' in df.columns else df['low'].min() if 'low' in df.columns else current_price
        
        # Handle NaN values safely
        volume_value = df['volume'].iloc[-1] if 'volume' in df.columns else 0
        volume_int = int(volume_value) if pd.notna(volume_value) else 0
        
        hist_data = df[['open', 'high', 'low', 'close', 'volume']].tail(252) if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']) else df.iloc[:, :5].tail(252)
        
        return {
            'ticker': ticker,
            'name': stock_name,
            'current_price': current_price,
            'previous_close': prev_close,
            'change_percent': round(change_pct, 2) if pd.notna(change_pct) else 0,
            'volume': volume_int,
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'beta': 1.0,
            'volatility': round(volatility, 2) if pd.notna(volatility) else 0,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'returns_1m': round(returns_1m, 2) if pd.notna(returns_1m) else 0,
            'returns_3m': round(returns_3m, 2) if pd.notna(returns_3m) else 0,
            'returns_6m': round(returns_6m, 2) if pd.notna(returns_6m) else 0,
            'returns_1y': round(returns_1y, 2) if pd.notna(returns_1y) else 0,
            'historical': hist_data,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'last_updated': datetime.now()
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
        return None

def get_stock_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock data for a specific ticker"""
    _initialize_stock_data()
    
    # First check if it's in the preloaded top 20 stocks
    if 'top_stocks_data' in st.session_state and ticker in st.session_state.top_stocks_data:
        return st.session_state.top_stocks_data[ticker]
    
    # Otherwise fetch it individually
    return _fetch_single_stock_yfinance(ticker)

def get_multiple_stocks(tickers: List[str], use_cache: bool = True) -> Dict[str, Optional[Dict]]:
    """Get multiple stocks"""
    _initialize_stock_data()
    
    results = {}
    if 'top_stocks_data' in st.session_state:
        for ticker in tickers:
            if ticker in st.session_state.top_stocks_data:
                results[ticker] = st.session_state.top_stocks_data[ticker]
    
    return results

def get_all_stocks() -> Dict[str, Optional[Dict]]:
    """Get all top 20 stocks with their data"""
    _initialize_stock_data()
    
    # Wait for data to be loaded
    max_wait = 10  # Wait up to 10 seconds
    wait_count = 0
    while 'top_stocks_data' not in st.session_state and wait_count < max_wait:
        import time
        time.sleep(0.1)
        wait_count += 1
    
    if 'top_stocks_data' in st.session_state and len(st.session_state.top_stocks_data) > 0:
        return st.session_state.top_stocks_data
    
    return {}

def show_api_usage_stats():
    """Display API usage statistics in sidebar (removed for cleaner UI)"""
    pass
