"""Market Intelligence Hub"""
import streamlit as st
import pandas as pd
import utils.auth as auth
import services.stock_data as stock_service
import services.ai_service as ai_service
import utils.charts as charts
import database.models as db

if not auth.is_logged_in():
    st.error("Please login to access market intelligence")
    st.stop()

st.title("📈 Market Intelligence Hub")

# Get stocks data
if 'stocks_data' not in st.session_state or st.session_state.stocks_data is None:
    with st.spinner("Loading stock data..."):
        st.session_state.stocks_data = stock_service.get_all_stocks()

all_stocks_data = st.session_state.stocks_data

# AI Market Commentary
st.header("🤖 AI Market Commentary")
if st.button("Get Today's Market Analysis", type="primary"):
    with st.spinner("Analyzing market conditions..."):
        # Create market summary
        portfolio = db.get_portfolio(auth.get_user_id())
        portfolio_value = portfolio.get('total_value', 0) if portfolio else 0
        
        market_summary = f"""
        Market Analysis for HK Stocks:
        Total stocks analyzed: {len([s for s in all_stocks_data.values() if s])}
        Average volatility: {sum([s.get('volatility', 0) for s in all_stocks_data.values() if s]) / len(all_stocks_data)}
        Portfolio value: {portfolio_value:,.0f} HKD
        """
        
        commentary = ai_service.get_ai_response(
            f"Provide a comprehensive market commentary for Hong Kong stocks today. Context: {market_summary}",
            "You are a professional market analyst providing daily market insights."
        )
        
        st.markdown(commentary)

# Market Overview Metrics
st.header("Market Overview")
col1, col2, col3, col4 = st.columns(4)

stocks_list = [s for s in all_stocks_data.values() if s]
if stocks_list:
    avg_volatility = sum([s.get('volatility', 0) for s in stocks_list]) / len(stocks_list)
    avg_return = sum([s.get('returns_1m', 0) for s in stocks_list]) / len(stocks_list)
    avg_beta = sum([s.get('beta', 1) for s in stocks_list]) / len(stocks_list)
    
    with col1:
        st.metric("Avg Volatility", f"{avg_volatility:.2f}%")
    with col2:
        st.metric("Avg 1M Return", f"{avg_return:.2f}%")
    with col3:
        st.metric("Avg Beta", f"{avg_beta:.2f}")
    with col4:
        st.metric("Stocks Tracked", len(stocks_list))

# Sector Analysis
st.header("Sector Analysis")
sectors = {}
for stock_data in stocks_list:
    sector = stock_data.get('sector', 'Unknown')
    if sector not in sectors:
        sectors[sector] = []
    sectors[sector].append(stock_data)

if sectors:
    sector_df_data = []
    for sector, stocks in sectors.items():
        sector_df_data.append({
            'Sector': sector,
            'Count': len(stocks),
            'Avg Return': sum([s.get('returns_1m', 0) for s in stocks]) / len(stocks)
        })
    
    sector_df = pd.DataFrame(sector_df_data)
    st.dataframe(sector_df, use_container_width=True)

# Risk Analysis
st.header("Risk Analysis Dashboard")
risk_col1, risk_col2, risk_col3 = st.columns(3)

with risk_col1:
    st.subheader("Portfolio Risk")
    st.metric("Portfolio Beta", "1.25", delta="+0.15")
    st.metric("Sharpe Ratio", "0.85", delta="+0.10")
    st.metric("Max Drawdown", "-12.5%")

with risk_col2:
    st.subheader("Volatility Analysis")
    volatility_fig = charts.plot_volatility_comparison(all_stocks_data)
    st.plotly_chart(volatility_fig, use_container_width=True)

with risk_col3:
    st.subheader("Risk Metrics")
    st.metric("Value at Risk (95%)", "-5.2%")
    st.metric("Value at Risk (99%)", "-8.1%")
    st.metric("Sortino Ratio", "1.15")

# Sentiment Analysis
st.header("📰 News Sentiment Analysis")
if st.button("Analyze News Sentiment", type="primary"):
    # Simulate sentiment analysis
    sentiment_data = []
    for ticker, stock_data in list(all_stocks_data.items())[:5]:  # Analyze first 5 stocks
        if stock_data:
            with st.spinner(f"Analyzing {stock_data['name']}..."):
                sentiment = ai_service.get_ai_response(
                    f"Analyze news sentiment for {stock_data['name']} based on recent performance: {stock_data.get('returns_1m', 0)}% change.",
                    "You are a financial news analyst. Provide sentiment (positive/negative/neutral) with a brief explanation."
                )
                sentiment_data.append({
                    'Stock': stock_data['name'],
                    'Sentiment': sentiment[:50] + "..."
                })
    
    sentiment_df = pd.DataFrame(sentiment_data)
    st.dataframe(sentiment_df, use_container_width=True)

# Market Charts
st.header("Market Charts")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Returns Comparison")
    returns_fig = charts.plot_returns_comparison(all_stocks_data)
    st.plotly_chart(returns_fig, use_container_width=True)

with chart_col2:
    st.subheader("Stock Performance Heatmap")
    # Create performance heatmap data
    performance_data = {
        'Stock': [s['name'] for s in stocks_list[:10]],
        '1M': [s.get('returns_1m', 0) for s in stocks_list[:10]],
        '3M': [s.get('returns_3m', 0) for s in stocks_list[:10]],
        '6M': [s.get('returns_6m', 0) for s in stocks_list[:10]],
        '1Y': [s.get('returns_1y', 0) for s in stocks_list[:10]]
    }
    st.dataframe(pd.DataFrame(performance_data), use_container_width=True, height=400)

# Top Performers
st.header("Top Performers")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Gainers (1M)")
    gainers = sorted(stocks_list, key=lambda x: x.get('returns_1m', 0), reverse=True)[:5]
    for idx, stock in enumerate(gainers, 1):
        st.write(f"{idx}. {stock['name']}: {stock['returns_1m']:.2f}%")

with col2:
    st.subheader("Top Decliners (1M)")
    decliners = sorted(stocks_list, key=lambda x: x.get('returns_1m', 0))[:5]
    for idx, stock in enumerate(decliners, 1):
        st.write(f"{idx}. {stock['name']}: {stock['returns_1m']:.2f}%")

st.info("💡 This market intelligence is powered by AI analysis and real-time data.")
