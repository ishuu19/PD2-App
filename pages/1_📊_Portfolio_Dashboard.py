"""Portfolio Dashboard - Main trading interface"""
import streamlit as st
import pandas as pd
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
import services.portfolio_service as portfolio_service
import services.ai_service as ai_service
import utils.charts as charts
from config import constants

# Check authentication
if not auth.is_logged_in():
    st.error("Please login to access the portfolio dashboard")
    st.stop()

st.title("📊 Portfolio Dashboard")

user_id = auth.get_user_id()

# Ensure stocks data is loaded
if 'stocks_data' not in st.session_state or st.session_state.stocks_data is None:
    with st.spinner("Loading stock data..."):
        st.session_state.stocks_data = stock_service.get_all_stocks()

all_stocks_data = st.session_state.stocks_data

# Portfolio Summary Section
st.header("Portfolio Summary")
col1, col2, col3, col4 = st.columns(4)

portfolio = db.get_portfolio(user_id)
portfolio_value = portfolio_service.calculate_portfolio_value(user_id, all_stocks_data)

if portfolio_value:
    with col1:
        st.metric("Cash Balance", f"{portfolio_value.get('cash', 0):,.0f} HKD")
    with col2:
        st.metric("Stock Value", f"{portfolio_value.get('total_stock_value', 0):,.0f} HKD")
    with col3:
        st.metric("Total Value", f"{portfolio_value.get('total_value', 0):,.0f} HKD")
    with col4:
        total_return = portfolio_service.calculate_portfolio_return(user_id)
        st.metric("Total Return", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")

# Portfolio Holdings Section
st.header("Your Holdings")
holdings = portfolio_value.get('holdings', []) if portfolio_value else []

if holdings:
    holdings_df = pd.DataFrame(holdings)
    st.dataframe(holdings_df[['name', 'quantity', 'current_price', 'value', 'change_percent']], 
                 use_container_width=True)
    
    # Portfolio Allocation Chart
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.plot_portfolio_allocation(holdings)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("You don't have any holdings yet. Buy some stocks below!")

# All Stocks Section
st.header("Available Stocks (Hong Kong Market)")
st.markdown("Select stocks from 20 pre-selected Hong Kong stocks to invest in.")

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
        
        st.info(f"**{stock_data['name']} ({selected_ticker})** - Current Price: {current_price:.2f} HKD")
        
        quantity = st.number_input("Quantity", min_value=1, value=100, key="buy_quantity")
        
        total_cost = quantity * current_price
        
        st.metric("Total Cost", f"{total_cost:,.0f} HKD")
        
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
                stock_data = all_stocks_data.get(selected_sell_ticker, {})
                current_price = stock_data.get('current_price', holding['current_price'])
                
                st.info(f"**{holding['name']} ({selected_sell_ticker})** - You own {holding['quantity']} shares")
                st.info(f"Current Price: {current_price:.2f} HKD")
                
                max_quantity = int(holding['quantity'])
                quantity = st.number_input("Quantity to Sell", min_value=1, max_value=max_quantity, value=1, key="sell_quantity")
                
                total_proceeds = quantity * current_price
                
                st.metric("Total Proceeds", f"{total_proceeds:,.0f} HKD")
                
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
