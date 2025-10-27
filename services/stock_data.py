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

def _get_random_api_key() -> str:
    """Get a random API key from the list of available keys"""
    try:
        import random
        api_keys = keys.get_alpha_vantage_api_keys()
        if api_keys and len(api_keys) > 0:
            return random.choice(api_keys)
        else:
            return keys.get_alpha_vantage_api_key()  # Fallback to single key
    except:
        return keys.get_alpha_vantage_api_key()  # Fallback to single key

def _log_api_usage(api_key: str, ticker: str, success: bool):
    """Log API key usage for monitoring"""
    if 'api_usage_log' not in st.session_state:
        st.session_state.api_usage_log = {}
    
    key_short = api_key[:8] + "..."
    if key_short not in st.session_state.api_usage_log:
        st.session_state.api_usage_log[key_short] = {'success': 0, 'failed': 0, 'tickers': set()}
    
    if success:
        st.session_state.api_usage_log[key_short]['success'] += 1
    else:
        st.session_state.api_usage_log[key_short]['failed'] += 1
    
    st.session_state.api_usage_log[key_short]['tickers'].add(ticker)

def _fetch_ticker_alphavantage(ticker: str, max_retries: int = 3) -> Optional[Dict]:
    """Fetch ticker data from Alpha Vantage API with random key selection and retry logic"""
    api_keys = keys.get_alpha_vantage_api_keys()
    
    if not api_keys:
        st.error("No Alpha Vantage API keys configured")
        return None
    
    # Debug mode check (use session state to avoid duplicate widgets)
    if 'debug_api_keys_global' not in st.session_state:
        st.session_state.debug_api_keys_global = False
    debug_mode = st.session_state.debug_api_keys_global
    
    # Try with different API keys if one fails
    for attempt in range(max_retries):
        try:
            _rate_limit()
            
            # Get a random API key from the pool
            api_key = api_keys[attempt % len(api_keys)]  # Cycle through keys
            
            # Show debug info if enabled
            if debug_mode:
                st.sidebar.write(f"Attempt {attempt + 1}: Using API key: {api_key[:8]}...")
            
            # Log API key usage
            _log_api_usage(api_key, ticker, False)  # Will be updated to True if successful
            
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
                if attempt < max_retries - 1:
                    continue  # Try next API key
                st.error(f"Error fetching {ticker}: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                if attempt < max_retries - 1:
                    continue  # Try next API key
                st.error(f"Alpha Vantage error for {ticker}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                if attempt < max_retries - 1:
                    continue  # Try next API key
                st.error(f"Rate limit exceeded for {ticker}")
                return None
            
            if 'Time Series (Daily)' not in data:
                if attempt < max_retries - 1:
                    continue  # Try next API key
                st.error(f"No data returned for {ticker}")
                return None
            
            # If we reach here, we have valid data
            _log_api_usage(api_key, ticker, True)  # Update to successful
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
            if attempt < max_retries - 1:
                continue  # Try next API key
            st.error(f"Error fetching {ticker} from Alpha Vantage: {str(e)}")
            return None
    
    # If we get here, all attempts failed
    st.error(f"Failed to fetch {ticker} after {max_retries} attempts")
    return None

def get_stock_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock data with caching"""
    # Check session state first (in-memory cache with full data)
    cache_key = f"stock_{ticker}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # Check database cache for basic metrics only
    if use_cache:
        cached_data = db.get_cached_stock_data(ticker)
        if cached_data:
            # If we have cached basic data, we still need to fetch fresh data for historical
            # This ensures we always have historical data for predictions
            pass
    
    # Fetch from API (always get fresh data to ensure historical data is available)
    data = _fetch_ticker_alphavantage(ticker)
    
    if data:
        # Cache in session state (with full data including historical)
        st.session_state[cache_key] = data
        
        # Prepare data for database (remove pandas DataFrame)
        data_for_cache = data.copy()
        if 'historical' in data_for_cache:
            # Remove historical DataFrame - can't store in MongoDB
            del data_for_cache['historical']
        
        # Cache basic metrics in database
        db.cache_stock_data(ticker, data_for_cache)
    
    return data

def get_multiple_stocks(tickers: List[str], use_cache: bool = True) -> Dict[str, Optional[Dict]]:
    """Get multiple stocks efficiently with better caching"""
    results = {}
    
    # Check session state first for all tickers
    for ticker in tickers:
        cache_key = f"stock_{ticker}"
        if cache_key in st.session_state:
            results[ticker] = st.session_state[cache_key]
        else:
            # Fetch fresh data to ensure historical data is available
            results[ticker] = get_stock_data(ticker, use_cache=False)
    
    return results

def get_all_stocks() -> Dict[str, Optional[Dict]]:
    """Get all 20 pre-selected stocks"""
    return get_multiple_stocks(constants.HK_STOCKS)

def show_api_usage_stats():
    """Display API usage statistics in sidebar"""
    # Add debug checkbox (only create once)
    st.sidebar.checkbox("🔧 Debug API Keys", help="Show which API key is being used", key="debug_api_keys_global")
    
    if 'api_usage_log' in st.session_state and st.session_state.api_usage_log:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 API Usage Stats")
        
        for key_short, stats in st.session_state.api_usage_log.items():
            total = stats['success'] + stats['failed']
            success_rate = (stats['success'] / total * 100) if total > 0 else 0
            
            st.sidebar.write(f"**{key_short}**")
            st.sidebar.write(f"Success: {stats['success']} | Failed: {stats['failed']}")
            st.sidebar.write(f"Success Rate: {success_rate:.1f}%")
            st.sidebar.write(f"Tickers: {', '.join(list(stats['tickers'])[:3])}{'...' if len(stats['tickers']) > 3 else ''}")
            st.sidebar.write("---")
