"""Yahoo Finance Data Service with Caching and Error Handling"""
import yfinance as yf
import pandas as pd
import time
from typing import Dict, List, Optional
from retrying import retry
import streamlit as st
import database.models as db
from config import constants

# Rate limiting
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 2.0  # Minimum 2 seconds between requests (30 requests per minute max)

def _rate_limit():
    """Rate limiting to avoid too many requests"""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def _fetch_ticker_safe(ticker: str) -> Optional[Dict]:
    """Fetch ticker data with retry logic"""
    try:
        _rate_limit()
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data
        hist = stock.history(period="1y")
        
        if hist.empty or not info:
            return None
        
        # Calculate metrics
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        prev_close = info.get('previousClose', current_price)
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        
        # Calculate historical returns
        returns_1m = hist['Close'].pct_change(20).iloc[-1] * 100 if len(hist) > 20 else 0
        returns_3m = hist['Close'].pct_change(60).iloc[-1] * 100 if len(hist) > 60 else 0
        returns_6m = hist['Close'].pct_change(120).iloc[-1] * 100 if len(hist) > 120 else 0
        returns_1y = hist['Close'].pct_change(252).iloc[-1] * 100 if len(hist) > 252 else 0
        
        # Volatility (annualized)
        volatility = hist['Close'].pct_change().std() * (252 ** 0.5) * 100
        
        # 52-week high/low
        high_52w = hist['High'].max()
        low_52w = hist['Low'].min()
        
        data = {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'current_price': current_price,
            'previous_close': prev_close,
            'change_percent': round(change_pct, 2),
            'volume': info.get('volume', hist['Volume'].iloc[-1]),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'beta': info.get('beta', 1.0),
            'volatility': round(volatility, 2),
            'high_52w': high_52w,
            'low_52w': low_52w,
            'returns_1m': round(returns_1m, 2),
            'returns_3m': round(returns_3m, 2),
            'returns_6m': round(returns_6m, 2),
            'returns_1y': round(returns_1y, 2),
            'historical': hist,
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown')
        }
        
        return data
        
    except Exception as e:
        st.error(f"Error fetching {ticker}: {str(e)}")
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
    data = _fetch_ticker_safe(ticker)
    
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
