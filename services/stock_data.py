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

# Debug toggle for step-by-step metric calculations
DEBUG_STOCKS = True

# Simple debug printer
def _dbg(msg: str):
    try:
        if DEBUG_STOCKS:
            pass  # Removed print statement
    except Exception:
        pass

# Helpers
def _first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    return None

# Create cache directory for storing data
if not os.path.exists('.yfinance_cache'):
    os.makedirs('.yfinance_cache')

def _load_stock_from_csv(ticker: str) -> Optional[pd.DataFrame]:
    """Load stock data from CSV file (disabled for deployment)"""
    # CSV loading disabled for Streamlit Cloud deployment
    # to avoid inotify watch limit issues
    return None

def _download_top_stocks_data():
    """Download 5+ years of historical data for top stocks using bulk download, store in variables, then combine."""
    tickers = constants.HK_STOCKS
    stocks_data = {}
    
    _dbg(f"Downloading data for {len(tickers)} stocks using bulk download...")

    # Download 5+ years of daily data (since 2018-01-01)
    start_date = "2018-01-01"
    end_date = None  # means up to today

    # Try bulk download first
    try:
        data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            interval='1d',
            group_by='ticker',
            auto_adjust=True,
            threads=True
        )
        
        # Debug: Print data structure
        _dbg(f"Bulk download completed. Data type: {type(data)}")
        _dbg(f"Data shape: {data.shape if hasattr(data, 'shape') else 'No shape'}")
        _dbg(f"Data columns: {list(data.columns) if hasattr(data, 'columns') else 'No columns'}")
        if hasattr(data, 'columns') and len(data.columns) > 0:
            _dbg(f"First few rows:\n{data.head()}")
        _dbg(f"Available tickers in data: {[t for t in tickers if t in data.columns.get_level_values(0)] if hasattr(data, 'columns') else 'No multiindex'}")
        
        # Check if we got any data
        if data is None or data.empty or len(data) == 0:
            _dbg("Bulk download returned empty data, falling back to individual downloads...")
            return _download_individual_stocks(tickers)
            
    except Exception as e:
        _dbg(f"Bulk download failed: {str(e)}")
        _dbg(f"Bulk download failed: {str(e)}, falling back to individual downloads...")
        return _download_individual_stocks(tickers)

    # Per-ticker DataFrames in memory
    stock_dfs = {}
    available = []

    # Process each stock like the CSV flow, but keep in variables
    for ticker in tickers:
        try:
            # Guard: make sure ticker data exists in the multiindex
            if hasattr(data, 'columns') and ticker in getattr(data.columns, 'levels', [data.columns])[0]:
                df = data[ticker].reset_index()
                _dbg(f"[{ticker}] Extracted from multiindex, shape: {df.shape}")
            else:
                # Fallback for some yfinance versions
                try:
                    df = data[ticker].reset_index()
                    _dbg(f"[{ticker}] Extracted from fallback, shape: {df.shape}")
                except Exception as e:
                    _dbg(f"[{ticker}] Failed to extract: {str(e)}")
                    _dbg(f"  No data for {ticker}")
                    continue
                
            if df.empty:
                _dbg(f"[{ticker}] DataFrame is empty")
                _dbg(f"  No data for {ticker}")
                continue

            # Debug: Print raw data before processing
            _dbg(f"[{ticker}] Raw data columns: {list(df.columns)}")
            _dbg(f"[{ticker}] Raw data head:\n{df.head()}")
            _dbg(f"[{ticker}] Raw data dtypes:\n{df.dtypes}")

            # Normalize columns and index
            df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            _dbg(f"[{ticker}] After processing - columns: {list(df.columns)}")
            _dbg(f"[{ticker}] After processing - shape: {df.shape}")
            _dbg(f"[{ticker}] After processing - head:\n{df.head()}")

            stock_dfs[ticker] = df
            available.append(ticker)

            # Transform into site-friendly metrics
            stock_data = _process_stock_data(ticker, df)
            if stock_data:
                stocks_data[ticker] = stock_data
                _dbg(f"  Loaded {ticker}: {len(df)} rows")

        except Exception as e:
            _dbg(f"  Failed to process {ticker}: {str(e)}")
            continue

    # Combined DataFrame in memory (optional)
    try:
        if len(available) > 0:
            combined_df = pd.concat(
                [stock_dfs[t].reset_index().assign(Ticker=t) for t in available],
                ignore_index=True
            )
        else:
            combined_df = pd.DataFrame()
    except Exception:
        combined_df = pd.DataFrame()

    # Expose variables to the app session
    try:
        st.session_state.stock_dfs = stock_dfs
        st.session_state.combined_df = combined_df
    except Exception:
        pass

    _dbg(f"\nSuccessfully processed {len(stocks_data)} stocks")
    return stocks_data

def _download_individual_stocks(tickers: List[str]) -> Dict:
    """Fallback method: Download stocks individually with delays"""
    stocks_data = {}
    
    _dbg(f"Downloading {len(tickers)} stocks individually...")
    
    for i, ticker in enumerate(tickers):
        try:
            _dbg(f"Downloading {ticker} ({i+1}/{len(tickers)})...")
            
            # Add delay to avoid rate limiting
            if i > 0:
                time.sleep(1)  # 1 second delay between downloads
            
            data = yf.download(
                ticker,
                start="2020-01-01",  # Shorter period for individual downloads
                end=None,
                interval='1d',
                progress=False,
                threads=False  # Disable threading for individual downloads
            )
            
            if data.empty:
                _dbg(f"  No data for {ticker}")
                continue
            
            # Process the data
            df = data.reset_index()
            df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            stock_data = _process_stock_data(ticker, df)
            if stock_data:
                stocks_data[ticker] = stock_data
                _dbg(f"  ✓ {ticker}: ${stock_data['current_price']:.2f}")
        
        except Exception as e:
            _dbg(f"  ✗ Failed to download {ticker}: {str(e)}")
            continue
    
    _dbg(f"Successfully processed {len(stocks_data)} stocks individually")
    return stocks_data

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
        
        # 52-week high/low (compute df_len locally for this function)
        df_len_local = len(df)
        high_52w = df['high'].tail(252).max() if df_len_local >= 252 and 'high' in df.columns else df['high'].max() if 'high' in df.columns else current_price
        low_52w = df['low'].tail(252).min() if df_len_local >= 252 and 'low' in df.columns else df['low'].min() if 'low' in df.columns else current_price
        
        # Handle NaN values safely
        volume_value = df['volume'].iloc[-1] if 'volume' in df.columns else 0
        volume_int = int(volume_value) if pd.notna(volume_value) else 0
        
        hist_data = df[['open', 'high', 'low', 'close', 'volume']].tail(252) if all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']) else df.iloc[:, :5].tail(252)
        
        result = {
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
        _dbg(f"[{ticker}] result summary: price={result['current_price']}, change%={result['change_percent']}, vol={result['volume']}")
        return result
    except Exception as e:
        _dbg(f"Error fetching {ticker}: {str(e)}")
        return None

def get_stock_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock data for a specific ticker"""
    _initialize_stock_data()
    
    # First check if it's in the preloaded top stocks
    if 'top_stocks_data' in st.session_state and ticker in st.session_state.top_stocks_data:
        return st.session_state.top_stocks_data[ticker]
    
    # Otherwise fetch it individually using bulk download for efficiency
    try:
        _dbg(f"Fetching individual stock data for {ticker}...")
        data = yf.download(
            ticker, 
            start="2018-01-01", 
            end=None, 
            interval='1d', 
            auto_adjust=True, 
            threads=True
        )
        
        if data.empty:
            _dbg(f"No data found for {ticker}")
            return None
        
        # Process the data
        df = data.reset_index()
        df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        return _process_stock_data(ticker, df)
        
    except Exception as e:
        _dbg(f"Error fetching {ticker}: {str(e)}")
        return None

def _process_stock_data(ticker: str, df: pd.DataFrame) -> Optional[Dict]:
    """Process stock data DataFrame into standardized format"""
    try:
        _dbg(f"[{ticker}] start processing")

        # Normalize canonical column names if needed
        # Sometimes yfinance returns 'Adj Close' or lowercase already
        col_map = {}
        if 'Adj Close'.lower() in df.columns:
            pass
        # ensure lowercase names for safety
        df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]

        # Choose columns
        close_col = _first_existing_column(df, ['close', 'adj close', 'adj_close'])
        open_col = _first_existing_column(df, ['open'])
        high_col = _first_existing_column(df, ['high'])
        low_col = _first_existing_column(df, ['low'])
        volume_col = _first_existing_column(df, ['volume'])

        if close_col is None:
            _dbg(f"[{ticker}] missing close column; columns={list(df.columns)}")
            return None

        # Get stock name
        stock_name = constants.STOCK_NAMES.get(ticker, ticker)

        # Current and previous close - get last valid values
        close_series = df[close_col].dropna()
        if close_series.empty:
            _dbg(f"[{ticker}] No valid close prices found")
            return None
            
        current_price = float(close_series.iloc[-1])
        prev_close = float(close_series.iloc[-2]) if len(close_series) > 1 else current_price
        change_pct = float(((current_price - prev_close) / prev_close * 100)) if prev_close not in (0, 0.0) else 0.0
        _dbg(f"[{ticker}] prices: current={current_price}, prev={prev_close}, change%={change_pct}")

        # Historical returns
        df_len = len(df)
        def pct_return(days: int) -> float:
            if df_len > days and close_col in df.columns:
                val = df[close_col].pct_change(days).iloc[-1]
                return float(val * 100) if pd.notna(val) else 0.0
            return 0.0
        returns_1m = pct_return(20)
        returns_3m = pct_return(60)
        returns_6m = pct_return(120)
        returns_1y = pct_return(252)
        _dbg(f"[{ticker}] returns: 1m={returns_1m}, 3m={returns_3m}, 6m={returns_6m}, 1y={returns_1y}")

        # Volatility (annualized)
        if close_col in df.columns:
            vol_series = df[close_col].pct_change()
            volatility = float(vol_series.std() * (252 ** 0.5) * 100) if vol_series.notna().sum() > 1 else 0.0
        else:
            volatility = 0.0
        _dbg(f"[{ticker}] volatility={volatility}")

        # 52-week high/low
        if high_col and high_col in df.columns:
            high_52w = float(df[high_col].tail(252).max()) if df_len >= 2 else float(df[high_col].max())
        else:
            high_52w = current_price
        if low_col and low_col in df.columns:
            low_52w = float(df[low_col].tail(252).min()) if df_len >= 2 else float(df[low_col].min())
        else:
            low_52w = current_price
        _dbg(f"[{ticker}] 52w: high={high_52w}, low={low_52w}")

        # Volume - get last valid volume
        if volume_col and volume_col in df.columns:
            volume_series = df[volume_col].dropna()
            if not volume_series.empty:
                volume_value = volume_series.iloc[-1]
                volume_int = int(volume_value) if pd.notna(volume_value) else 0
            else:
                volume_int = 0
        else:
            volume_int = 0
        _dbg(f"[{ticker}] volume={volume_int}")

        # Historical slice for charts
        if all(col in df.columns for col in [open_col or 'open', high_col or 'high', low_col or 'low', close_col or 'close', volume_col or 'volume']):
            cols = [open_col or 'open', high_col or 'high', low_col or 'low', close_col or 'close', volume_col or 'volume']
            hist_data = df[cols].tail(252)
        else:
            # fallback: take first up to 5 cols
            hist_data = df.iloc[:, :5].tail(252)
        _dbg(f"[{ticker}] hist rows={len(hist_data)}")
        
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
        _dbg(f"Error processing {ticker}: {str(e)}")
        return None

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
