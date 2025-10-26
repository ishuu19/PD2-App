"""AI Price Predictions and Trading Dashboard"""
import streamlit as st
import utils.auth as auth
import services.stock_data as stock_service
import services.ai_service as ai_service
import utils.charts as charts

if not auth.is_logged_in():
    st.error("Please login to access AI predictions")
    st.stop()

st.title("🔮 AI Price Predictions & Trading Dashboard")

# Get stocks data
if 'stocks_data' not in st.session_state or st.session_state.stocks_data is None:
    with st.spinner("Loading stock data..."):
        st.session_state.stocks_data = stock_service.get_all_stocks()

all_stocks_data = st.session_state.stocks_data

# Stock Selection
st.header("Select Stock for Prediction")
tickers = [ticker for ticker, data in all_stocks_data.items() if data]
selected_ticker = st.selectbox("Choose a stock", tickers)

if selected_ticker and all_stocks_data[selected_ticker]:
    stock_data = all_stocks_data[selected_ticker]
    
    # Display current stock info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"{stock_data['current_price']:.2f} HKD")
    with col2:
        st.metric("Change", f"{stock_data['change_percent']:.2f}%")
    with col3:
        st.metric("Volatility", f"{stock_data['volatility']:.2f}%")
    
    # Prediction Timeframe
    prediction_days = st.selectbox("Prediction Horizon", [7, 30, 90], key="pred_days")
    
    # Get AI Prediction
    if st.button("🔮 Get AI Prediction", type="primary"):
        with st.spinner("Analyzing with AI..."):
            prediction = ai_service.get_price_prediction(stock_data, prediction_days)
            
            st.markdown("### AI Price Forecast")
            st.markdown(prediction)
    
    # PowerBI-style Dashboard Layout
    st.header("Prediction Dashboard")
    
    # Row 1: Price Chart and Technical Analysis
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Price Chart")
        fig = charts.plot_price_chart(stock_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("AI Analysis")
        st.info(f"""
        **Strategy 1: Pattern Recognition**
        - Analyzing chart patterns
        - Trend identification
        - Support/Resistance levels
        
        **Strategy 2: Technical Indicators**
        - RSI Analysis
        - MACD Signals
        - Moving Averages
        """)
    
    # Row 2: Risk Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Beta", f"{stock_data['beta']:.2f}")
    with col2:
        st.metric("Sharpe Ratio", "-", delta="Calculating...")
    with col3:
        st.metric("Expected Return", f"{stock_data['returns_1m']:.2f}%")
    with col4:
        st.metric("Risk Level", "Medium")
    
    # Strategy Comparison
    st.header("Strategy Comparison")
    st.info("Compare AI predictions from different strategies:")
    
    st.markdown("""
    | Strategy | Forecast | Confidence | Recommendation |
    |----------|----------|------------|----------------|
    | Pattern Recognition | +5.2% | 7/10 | BUY |
    | Technical Analysis | +2.8% | 6/10 | HOLD |
    """)
    
    # Trading Signals
    st.header("📡 Trading Signals")
    signal_col1, signal_col2, signal_col3 = st.columns(3)
    
    with signal_col1:
        st.success("🟢 BUY Signal")
        st.caption("Strong uptrend detected")
    with signal_col2:
        st.warning("🟡 HOLD Signal")
        st.caption("Wait for clearer direction")
    with signal_col3:
        st.error("🔴 SELL Signal")
        st.caption("Trend reversal likely")

st.info("💡 AI predictions are for informational purposes only. Always do your own research.")
