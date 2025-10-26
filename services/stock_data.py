"""Alpha Vantage Data Service with Caching and Error Handling"""
import requests
import pandas as pd
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import streamlit as st
import database.models as db
import config.api_keys as keys
from config import constants

# Rate limiting
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 12.1  # 5 requests per minute max (12 seconds)

def _rate_limit():
    """Rate limiting for Alpha Vantage (5 requests/minute max)"""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()

def _fetch_ticker_alphavantage(ticker: str) -> Optional[Dict]:
    """Fetch ticker data from Alpha Vantage API"""
    try:
        _rate_limit()
        
        api_key = keys.get_alpha_vantage_api_key()
        if not api_key:
            st.error("Alpha Vantage API key not configured")
            return None
        
        # Get daily time series data (using free endpoint)
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': api_key,
            'outputsize': 'full'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            st.error(f"Error fetching {ticker}: HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            st.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
            return None
        
        if 'Note' in data:
            st.error(f"Rate limit exceeded for {ticker}")
            return None
        
        if 'Time Series (Daily)' not in data:
            st.error(f"No data returned for {ticker}")
            return None
        
        time_series = data['Time Series (Daily)']
        
        # Convert to DataFrame
        df = pd.DataFrame(time_series).T
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.sort_index()
        
        if df.empty:
            return None
        
        # Calculate metrics (use 'close' instead of 'adjusted_close')
        current_price = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2] if len(df) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        # Calculate historical returns
        returns_1m = df['close'].pct_change(20).iloc[-1] * 100 if len(df) > 20 else 0
        returns_3m = df['close'].pct_change(60).iloc[-1] * 100 if len(df) > 60 else 0
        returns_6m = df['close'].pct_change(120).iloc[-1] * 100 if len(df) > 120 else 0
        returns_1y = df['close'].pct_change(252).iloc[-1] * 100 if len(df) > 252 else 0
        
        # Volatility (annualized)
        volatility = df['close'].pct_change().std() * (252 ** 0.5) * 100
        
        # 52-week high/low
        high_52w = df['high'].tail(252).max() if len(df) >= 252 else df['high'].max()
        low_52w = df['low'].tail(252).min() if len(df) >= 252 else df['low'].min()
        
        # Get stock info (basic from ticker name)
        stock_name = constants.STOCK_NAMES.get(ticker, ticker)
        
        result_data = {
            'ticker': ticker,
            'name': stock_name,
            'current_price': current_price,
            'previous_close': prev_close,
            'change_percent': round(change_pct, 2),
            'volume': int(df['volume'].iloc[-1]),
            'market_cap': 0,  # Alpha Vantage free tier doesn't provide this
            'pe_ratio': 0,  # Alpha Vantage free tier doesn't provide this
            'dividend_yield': 0,  # Can calculate if needed
            'beta': 1.0,  # Default
            'volatility': round(volatility, 2),
            'high_52w': high_52w,
            'low_52w': low_52w,
            'returns_1m': round(returns_1m, 2),
            'returns_3m': round(returns_3m, 2),
            'returns_6m': round(returns_6m, 2),
            'returns_1y': round(returns_1y, 2),
            'historical': df[['open', 'high', 'low', 'close', 'volume']].tail(252),  # Keep 1 year for charts
            'sector': 'Unknown',
            'industry': 'Unknown'
        }
        
        return result_data
        
    except Exception as e:
        st.error(f"Error fetching {ticker} from Alpha Vantage: {str(e)}")
        return None

def get_stock_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock data with caching"""
    # Check cache first
    if use_cache:
        cached_data = db.get_cached_stock_data(ticker)
        if cached_data:
            return cached_data
    
    # Check session state (in-memory cache)
    cache_key = f"stock_{ticker}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Fetch from API
    data = _fetch_ticker_alphavantage(ticker)
    
    if data:
        # Cache in session state
        st.session_state[cache_key] = data
        
        # Prepare data for database (remove pandas DataFrame)
        data_for_cache = data.copy()
        if 'historical' in data_for_cache:
            # Remove historical DataFrame - can't store in MongoDB
            del data_for_cache['historical']
        
        # Cache in database
        db.cache_stock_data(ticker, data_for_cache)
    
    return data

def get_multiple_stocks(tickers: List[str], use_cache: bool = True) -> Dict[str, Optional[Dict]]:
    """Get multiple stocks efficiently with better caching"""
    results = {}
    
    # First, try to get all cached data
    for ticker in tickers:
        if use_cache:
            # Check session state first
            cache_key = f"stock_{ticker}"
            if cache_key in st.session_state:
                results[ticker] = st.session_state[cache_key]
                continue
            
            # Check database cache
            cached_data = db.get_cached_stock_data(ticker)
            if cached_data:
                # Store in session state for faster access
                st.session_state[cache_key] = cached_data
                results[ticker] = cached_data
                continue
        
        # If not cached, fetch from API (with rate limiting)
        results[ticker] = get_stock_data(ticker, use_cache=False)
    
    return results

def get_all_stocks() -> Dict[str, Optional[Dict]]:
    """Get all 20 pre-selected stocks"""
    return get_multiple_stocks(constants.HK_STOCKS)
