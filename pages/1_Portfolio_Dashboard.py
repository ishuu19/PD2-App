"""Portfolio Dashboard - Main trading interface"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
import services.portfolio_service as portfolio_service
import services.ai_service as ai_service
import utils.charts as charts
import components.chatbot as chatbot
from config import constants

# Show API usage stats
stock_service.show_api_usage_stats()

# Check authentication
if not auth.is_logged_in():
    st.error("Please login to access the portfolio dashboard")
    st.stop()

# Show chatbot popup if opened
if st.session_state.get('chatbot_open', False):
    chatbot.render_chatbot_popup()

st.title("📊 Portfolio Dashboard")

user_id = auth.get_user_id()

# Get all top 20 stocks data (loaded from yfinance)
# Show spinner while loading stock data
with st.spinner("Loading stock data..."):
    all_stocks_data = stock_service.get_all_stocks()

# Verify we got stock data
if not all_stocks_data:
    st.warning("⚠️ Stock data is loading. Please wait a moment and refresh.")
    st.stop()

# Get portfolio
portfolio = db.get_portfolio(user_id)

# Auto-refresh portfolio data on first load
if 'portfolio_refreshed' not in st.session_state:
    st.session_state.portfolio_refreshed = False

if not st.session_state.portfolio_refreshed and portfolio and portfolio.get('holdings'):
    st.session_state.portfolio_refreshed = True
    try:
        # Automatically refresh portfolio with latest prices
        refresh_result = portfolio_service.refresh_portfolio_data(user_id)
        if refresh_result:
            # Reload the page to show updated data
            st.rerun()
    except Exception as e:
        # Silently handle errors - don't block the UI
        pass

# Portfolio Summary Section
st.header("Portfolio Summary")

# Add refresh button
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Refresh All Data", help="Get latest stock prices and update portfolio"):
        with st.spinner("Refreshing stock data..."):
            try:
                refresh_result = portfolio_service.refresh_portfolio_data(user_id)
                if refresh_result:
                    st.success(f"✅ Refreshed {refresh_result['stocks_refreshed']} stocks")
                    # Update session state with fresh data
                    st.session_state.stocks_data = {}
                    st.rerun()
                else:
                    st.error("Failed to refresh data")
            except Exception as e:
                st.error(f"Error refreshing data: {str(e)}")

with col_info:
    portfolio = db.get_portfolio(user_id)
    if portfolio and 'last_refresh' in portfolio:
        last_refresh = portfolio['last_refresh']
        if isinstance(last_refresh, str):
            st.caption(f"Last updated: {last_refresh}")
        else:
            st.caption(f"Last updated: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

col1, col2, col3, col4 = st.columns(4)

portfolio_value = portfolio_service.calculate_portfolio_value(user_id, all_stocks_data)

if portfolio_value:
    with col1:
        st.metric("Cash Balance", f"{portfolio_value.get('cash', 0):,.0f} USD")
    with col2:
        st.metric("Stock Value", f"{portfolio_value.get('total_stock_value', 0):,.0f} USD")
    with col3:
        total_pnl = portfolio_value.get('total_unrealized_pnl', 0)
        pnl_percent = portfolio_value.get('total_return_percent', 0)
        st.metric(
            "Total P&L", 
            f"{total_pnl:,.0f} USD",
            delta=f"{pnl_percent:.2f}%"
        )
    with col4:
        total_value = portfolio_value.get('total_value', 0)
        initial_cash = constants.INITIAL_CASH
        total_return = ((total_value - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        st.metric("Total Return", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")

# Additional Performance Metrics
if portfolio_value and portfolio_value.get('holdings'):
    st.markdown("---")
    st.subheader("📈 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cost_basis = portfolio_value.get('total_cost_basis', 0)
        st.metric("Total Invested", f"${cost_basis:,.0f}")
    
    with col2:
        current_value = portfolio_value.get('total_stock_value', 0)
        st.metric("Current Value", f"${current_value:,.0f}")
    
    with col3:
        unrealized_pnl = portfolio_value.get('total_unrealized_pnl', 0)
        pnl_color = "normal" if unrealized_pnl >= 0 else "inverse"
        st.metric("Unrealized P&L", f"${unrealized_pnl:,.0f}", delta=f"{portfolio_value.get('total_return_percent', 0):.2f}%")
    
    with col4:
        num_holdings = len(portfolio_value.get('holdings', []))
        st.metric("Number of Holdings", f"{num_holdings}")

# Portfolio Holdings Section
st.header("Your Holdings")
holdings = portfolio_value.get('holdings', []) if portfolio_value else []

if holdings:
    holdings_df = pd.DataFrame(holdings)
    
    # Create a more detailed holdings display with P&L tracking
    display_columns = ['name', 'quantity', 'purchase_price', 'current_price', 'current_value', 'unrealized_pnl', 'pnl_percent', 'purchase_date']
    available_columns = [col for col in display_columns if col in holdings_df.columns]
    
    # Format the dataframe for better display
    formatted_df = holdings_df[available_columns].copy()
    
    # Format numeric columns
    if 'current_price' in formatted_df.columns:
        formatted_df['current_price'] = formatted_df['current_price'].apply(lambda x: f"${x:.2f}")
    if 'purchase_price' in formatted_df.columns:
        formatted_df['purchase_price'] = formatted_df['purchase_price'].apply(lambda x: f"${x:.2f}")
    if 'current_value' in formatted_df.columns:
        formatted_df['current_value'] = formatted_df['current_value'].apply(lambda x: f"${x:,.0f}")
    if 'unrealized_pnl' in formatted_df.columns:
        formatted_df['unrealized_pnl'] = formatted_df['unrealized_pnl'].apply(lambda x: f"${x:,.0f}")
    if 'pnl_percent' in formatted_df.columns:
        formatted_df['pnl_percent'] = formatted_df['pnl_percent'].apply(lambda x: f"{x:.2f}%")
    if 'purchase_date' in formatted_df.columns:
        def format_date(date_val):
            if date_val == 'Unknown' or pd.isna(date_val):
                return 'N/A'
            try:
                return date_val.strftime('%Y-%m-%d')
            except:
                return str(date_val)
        formatted_df['purchase_date'] = formatted_df['purchase_date'].apply(format_date)
    
    # Rename columns for better display
    column_names = {
        'name': 'Stock Name',
        'quantity': 'Shares',
        'purchase_price': 'Purchase Price',
        'current_price': 'Current Price',
        'current_value': 'Current Value',
        'unrealized_pnl': 'Gain/Loss ($)',
        'pnl_percent': 'Gain/Loss (%)',
        'purchase_date': 'Purchase Date'
    }
    
    formatted_df = formatted_df.rename(columns=column_names)
    st.dataframe(formatted_df, use_container_width=True)
    
    # Portfolio Charts
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.plot_portfolio_allocation(holdings)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # P&L Chart
        if 'unrealized_pnl' in holdings_df.columns and 'name' in holdings_df.columns:
            fig_pnl = go.Figure()
            
            # Color bars based on P&L (green for positive, red for negative)
            colors = ['green' if pnl >= 0 else 'red' for pnl in holdings_df['unrealized_pnl']]
            
            fig_pnl.add_trace(go.Bar(
                x=holdings_df['name'],
                y=holdings_df['unrealized_pnl'],
                marker_color=colors,
                text=[f"${pnl:,.0f}" for pnl in holdings_df['unrealized_pnl']],
                textposition='auto'
            ))
            
            fig_pnl.update_layout(
                title="Portfolio P&L by Stock",
                xaxis_title="Stock",
                yaxis_title="Unrealized P&L ($)",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig_pnl, use_container_width=True)
else:
    st.info("You don't have any holdings yet. Buy some stocks below!")

# All Stocks Section
st.header("Available Stocks (US Market)")
st.markdown("Select stocks from 20 well-known US stocks to invest in.")

# Filter and search
search_term = st.text_input("🔍 Search stocks by name or ticker", key="stock_search")

# Prepare stock data for display
stock_display_data = []
for ticker, stock_data in all_stocks_data.items():
    if stock_data:
        if not search_term or search_term.lower() in stock_data['name'].lower() or search_term.lower() in ticker.lower():
            stock_display_data.append({
                'Ticker': ticker,
                'Name': stock_data['name'],
                'Price': stock_data['current_price'],
                'Change %': stock_data['change_percent'],
                'Volume': stock_data['volume'],
                'Market Cap': stock_data['market_cap'],
                'P/E': stock_data['pe_ratio'],
                'Div Yield %': stock_data['dividend_yield'],
                'Beta': stock_data['beta'],
                'Volatility %': stock_data['volatility'],
                'Returns 1M': stock_data['returns_1m'],
                'Returns 3M': stock_data['returns_3m'],
                'Returns 1Y': stock_data['returns_1y']
            })

if stock_display_data:
    st.dataframe(pd.DataFrame(stock_display_data), use_container_width=True, height=400)
else:
    st.warning("No stocks found matching your search.")

# Buy/Sell Section
st.header("Trade Stocks")
trading_tabs = st.tabs(["Buy", "Sell"])

with trading_tabs[0]:
    # Buy tab
    tickers = [ticker for ticker, data in all_stocks_data.items() if data]
    selected_ticker = st.selectbox("Select Stock to Buy", tickers, key="buy_ticker")
    
    if selected_ticker and all_stocks_data[selected_ticker]:
        stock_data = all_stocks_data[selected_ticker]
        current_price = stock_data['current_price']
        
        st.info(f"**{stock_data['name']} ({selected_ticker})** - Current Price: ${current_price:.2f} USD")
        
        quantity = st.number_input("Quantity", min_value=1, value=100, key="buy_quantity")
        
        total_cost = quantity * current_price
        
        st.metric("Total Cost", f"${total_cost:,.0f} USD")
        
        if st.button("🛒 Buy Stock", type="primary"):
            if portfolio_service.execute_buy(user_id, selected_ticker, current_price, quantity):
                st.success(f"Successfully bought {quantity} shares of {stock_data['name']}!")
                st.rerun()
            else:
                st.error("Transaction failed. Check your cash balance.")

with trading_tabs[1]:
    # Sell tab
    holdings_tickers = [h['ticker'] for h in holdings]
    
    if holdings_tickers:
        selected_sell_ticker = st.selectbox("Select Stock to Sell", holdings_tickers, key="sell_ticker")
        
        if selected_sell_ticker:
            # Get holding details
            holding = next((h for h in holdings if h['ticker'] == selected_sell_ticker), None)
            
            if holding:
                # Always get the current market price from stock data, not from holding
                stock_data = all_stocks_data.get(selected_sell_ticker, {})
                
                # Ensure we have current price from stock data, not purchase price
                if stock_data and 'current_price' in stock_data:
                    current_price = stock_data['current_price']
                else:
                    # If stock data is not available, fetch it fresh
                    fresh_stock_data = stock_service.get_stock_data(selected_sell_ticker, use_cache=False)
                    if fresh_stock_data and 'current_price' in fresh_stock_data:
                        current_price = fresh_stock_data['current_price']
                    else:
                        st.error(f"Unable to fetch current price for {selected_sell_ticker}. Please try again.")
                        current_price = None
                
                if current_price:
                    st.info(f"**{holding['name']} ({selected_sell_ticker})** - You own {holding['quantity']} shares")
                    st.info(f"Current Price: ${current_price:.2f} USD")
                    
                    max_quantity = int(holding['quantity'])
                    quantity = st.number_input("Quantity to Sell", min_value=1, max_value=max_quantity, value=1, key="sell_quantity")
                    
                    total_proceeds = quantity * current_price
                    
                    st.metric("Total Proceeds", f"${total_proceeds:,.0f} USD")
                    
                    if st.button("💰 Sell Stock", type="primary"):
                        if portfolio_service.execute_sell(user_id, selected_sell_ticker, current_price, quantity):
                            st.success(f"Successfully sold {quantity} shares of {holding['name']}!")
                            st.rerun()
                        else:
                            st.error("Transaction failed.")
    else:
        st.info("You don't have any holdings to sell.")

# AI Recommendations Section
st.header("🤖 AI Investment Recommendations")

if st.button("Get AI Recommendations", type="primary"):
    with st.spinner("Analyzing your portfolio with AI..."):
        # Prepare portfolio summary for AI
        portfolio_summary = {
            'cash': portfolio_value.get('cash', 0) if portfolio_value else 0,
            'total_value': portfolio_value.get('total_value', 0) if portfolio_value else 0,
            'total_return': portfolio_service.calculate_portfolio_return(user_id),
            'holdings': {h['ticker']: h['quantity'] for h in holdings}
        }
        
        ai_recommendations = ai_service.get_portfolio_recommendations(portfolio_summary)
        
        st.markdown("### AI Portfolio Analysis")
        st.markdown(ai_recommendations)

# Charts Section
st.header("Market Overview Charts")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Stock Returns Comparison")
    returns_fig = charts.plot_returns_comparison(all_stocks_data)
    st.plotly_chart(returns_fig, use_container_width=True)

with chart_col2:
    st.subheader("Volatility Comparison")
    volatility_fig = charts.plot_volatility_comparison(all_stocks_data)
    st.plotly_chart(volatility_fig, use_container_width=True)

# Transaction History
st.header("Transaction History")
transactions = db.get_transactions(user_id, limit=20)

if transactions:
    trans_data = []
    for t in transactions:
        trans_data.append({
            'Date': t['timestamp'].strftime('%Y-%m-%d %H:%M') if 'timestamp' in t else 'N/A',
            'Type': t['type'].upper(),
            'Ticker': t['ticker'],
            'Quantity': t['quantity'],
            'Price': f"{t['price']:.2f}",
            'Total': f"{(t['quantity'] * t['price']):,.0f}"
        })
    
    st.dataframe(pd.DataFrame(trans_data), use_container_width=True)
else:
    st.info("No transactions yet.")
