"""Chart Utilities using Plotly"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional

def plot_price_chart(stock_data: Dict) -> go.Figure:
    """Plot price chart with candlesticks"""
    if not stock_data or 'historical' not in stock_data:
        return go.Figure()
    
    hist = stock_data['historical']
    
    # Alpha Vantage uses lowercase column names
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist['open'],
        high=hist['high'],
        low=hist['low'],
        close=hist['close']
    )])
    
    fig.update_layout(
        title=f"{stock_data.get('name', 'Stock')} Price Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=400
    )
    
    return fig

def plot_portfolio_allocation(holdings: List[Dict]) -> go.Figure:
    """Plot portfolio allocation pie chart"""
    if not holdings:
        return go.Figure()
    
    labels = [h['name'] for h in holdings]
    # Use 'current_value' if available, otherwise fall back to 'value'
    values = [h.get('current_value', h.get('value', 0)) for h in holdings]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4
    )])
    
    fig.update_layout(
        title="Portfolio Allocation",
        template="plotly_dark",
        height=400
    )
    
    return fig

def plot_returns_comparison(all_stock_data: Dict[str, Dict]) -> go.Figure:
    """Plot returns comparison bar chart"""
    if not all_stock_data:
        return go.Figure()
    
    data = []
    for ticker, stock_data in all_stock_data.items():
        if stock_data:
            data.append({
                'Stock': stock_data.get('name', ticker),
                '1M Return %': stock_data.get('returns_1m', 0),
                '3M Return %': stock_data.get('returns_3m', 0),
                '6M Return %': stock_data.get('returns_6m', 0),
                '1Y Return %': stock_data.get('returns_1y', 0)
            })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    for period in ['1M Return %', '3M Return %', '6M Return %', '1Y Return %']:
        fig.add_trace(go.Bar(
            name=period,
            x=df['Stock'],
            y=df[period]
        ))
    
    fig.update_layout(
        title="Stock Returns Comparison",
        xaxis_title="Stock",
        yaxis_title="Return (%)",
        template="plotly_dark",
        barmode='group',
        height=500
    )
    
    return fig

def plot_volatility_comparison(all_stock_data: Dict[str, Dict]) -> go.Figure:
    """Plot volatility comparison"""
    if not all_stock_data:
        return go.Figure()
    
    stocks = []
    volatilities = []
    
    for ticker, stock_data in all_stock_data.items():
        if stock_data:
            stocks.append(stock_data.get('name', ticker))
            volatilities.append(stock_data.get('volatility', 0))
    
    fig = go.Figure(data=[go.Bar(
        x=stocks,
        y=volatilities,
        marker_color='purple'
    )])
    
    fig.update_layout(
        title="Stock Volatility Comparison",
        xaxis_title="Stock",
        yaxis_title="Volatility (%)",
        template="plotly_dark",
        height=400
    )
    
    return fig
