"""AI Price Predictions and Trading Dashboard - Statistical Forecasting"""
import streamlit as st
import utils.auth as auth
import services.stock_data as stock_service
import utils.charts as charts
import utils.predictions as pred
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Show API usage stats
stock_service.show_api_usage_stats()

if not auth.is_logged_in():
    st.error("Please login to access AI predictions")
    st.stop()

st.title("🔮 AI Price Predictions & Trading Dashboard")

# Ensure stocks_data is initialized
if 'stocks_data' not in st.session_state:
    st.session_state.stocks_data = {}

all_stocks_data = st.session_state.stocks_data

# Stock Selection
st.header("Select Stock for Prediction")
st.markdown("Choose from the top 20 US stocks for AI predictions.")

# Create dropdown with top 20 stocks
from config import constants
available_tickers = constants.HK_STOCKS
selected_ticker = st.selectbox(
    "🔍 Select a stock ticker for prediction", 
    available_tickers,
    key="prediction_ticker_dropdown",
    help="Choose from the top 20 well-known US stocks"
)

# Load data for selected ticker if not already loaded
if selected_ticker:
    if selected_ticker not in all_stocks_data or not all_stocks_data[selected_ticker]:
        with st.spinner(f"Loading data for {selected_ticker}..."):
            stock_data = stock_service.get_stock_data(selected_ticker)
            if stock_data:
                st.session_state.stocks_data[selected_ticker] = stock_data
                all_stocks_data = st.session_state.stocks_data
            else:
                st.error(f"Failed to load data for {selected_ticker}. Please try again.")
                st.stop()
    else:
        stock_data = all_stocks_data[selected_ticker]
    
    # Debug: Check if historical data is available
    if 'historical' not in stock_data or stock_data['historical'] is None:
        st.error(f"No historical data available for {selected_ticker}. Please try selecting a different stock or refresh the page.")
        # Debug information
        st.write("**Debug Info:**")
        st.write(f"Available keys in stock_data: {list(stock_data.keys())}")
        st.write(f"Stock data type: {type(stock_data)}")
        st.stop()
    elif len(stock_data['historical']) < 20:
        st.warning(f"Limited historical data available for {selected_ticker} ({len(stock_data['historical'])} days). Predictions may be less accurate.")
        # Show some debug info
        st.write(f"**Debug Info:** Historical data shape: {stock_data['historical'].shape if hasattr(stock_data['historical'], 'shape') else 'No shape attribute'}")
else:
    st.info("Please select a stock ticker from the dropdown above.")
    st.stop()

if selected_ticker and selected_ticker in all_stocks_data and all_stocks_data[selected_ticker]:
    stock_data = all_stocks_data[selected_ticker]
    
    # Display current stock info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${stock_data['current_price']:.2f}")
    with col2:
        st.metric("Change %", f"{stock_data['change_percent']:.2f}%", 
                  delta=f"{stock_data['change_percent']:.2f}%")
    with col3:
        st.metric("Volume", f"{stock_data['volume']:,}")
    with col4:
        st.metric("Volatility", f"{stock_data['volatility']:.2f}%")
    
    # Prediction Timeframe
    st.markdown("---")
    prediction_days = st.selectbox("Prediction Horizon", [7, 30, 90], key="pred_days")
    
    # Generate Prediction
    if st.button("🔮 Generate Statistical Forecast", type="primary", use_container_width=True):
        with st.spinner(f"🔮 Analyzing with statistical models for {prediction_days} days... This may take a moment."):
            try:
                forecast = pred.generate_forecast(stock_data, prediction_days)
                
                if 'error' in forecast:
                    st.error(forecast['error'])
                else:
                    st.session_state['forecast'] = forecast
                    st.success("✅ Forecast generated successfully!")
            except Exception as e:
                st.error(f"Error generating forecast: {str(e)}")
                st.session_state['forecast'] = None
    
    # Display Forecast Results
    if 'forecast' in st.session_state:
        forecast = st.session_state['forecast']
        
        # Check if forecast has required keys
        if 'error' in forecast:
            st.error(f"Forecast Error: {forecast['error']}")
        elif not forecast or 'average_forecast' not in forecast:
            st.error("Invalid forecast data. Please try generating the forecast again.")
        else:
            # Overall Prediction Summary
            st.markdown("---")
            st.header("📊 Forecast Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_forecast = forecast.get('average_forecast', 0)
                avg_change = forecast.get('average_change_percent', 0)
                st.metric("Average Forecast", f"${avg_forecast:.2f}",
                         delta=f"{avg_change:.2f}%")
            with col2:
                # Recommendation Badge
                rec = forecast.get('recommendation', 'HOLD')
                if 'STRONG BUY' in rec:
                    st.metric("Recommendation", rec, delta="Strong Buy")
                elif 'BUY' in rec:
                    st.metric("Recommendation", rec, delta="Buy")
                elif 'HOLD' in rec:
                    st.metric("Recommendation", rec, delta="Hold")
                elif 'SELL' in rec and 'STRONG' not in rec:
                    st.metric("Recommendation", rec, delta="Sell", delta_color="inverse")
                else:
                    st.metric("Recommendation", rec, delta="Strong Sell", delta_color="inverse")
            with col3:
                trend = forecast.get('trend', {})
                direction = trend.get('direction', 'neutral').upper()
                st.metric("Trend Direction", direction)
            with col4:
                strength = trend.get('strength', 0) * 100
                st.metric("Trend Strength", f"{strength:.1f}%")
        
            # Strategy Comparison
            st.markdown("---")
            st.header("📈 Advanced Model Comparison")
            
            strategies = forecast.get('strategies', {})
            ensemble = forecast.get('ensemble', {})
            
            if strategies:
                # Display ensemble result first
                if ensemble:
                    st.subheader("🎯 Ensemble Prediction (Weighted Average)")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Ensemble Forecast", f"${ensemble.get('prediction', 0):.2f}")
                    with col2:
                        st.metric("Confidence", f"{ensemble.get('confidence', 0)*100:.1f}%")
                    with col3:
                        models_used = ensemble.get('models_used', len(strategies))
                        st.metric("Models Used", f"{models_used}")
                    
                    st.caption("🎯 Ensemble combines multiple models with confidence weighting")
                
                # Display individual models
                st.subheader("🔬 Individual Model Results")
                
                # Create columns for models
                model_cols = st.columns(min(len(strategies), 3))
                
                for i, (model_name, model_data) in enumerate(strategies.items()):
                    if i < len(model_cols):
                        with model_cols[i]:
                            model_display_name = {
                                'arima': 'ARIMA',
                                'prophet': 'Prophet',
                                'holt_winters': 'Holt-Winters',
                                'lstm': 'LSTM Neural Network',
                                'monte_carlo': 'Monte Carlo'
                            }.get(model_name, model_name.upper())
                            
                            st.write(f"**{model_display_name}**")
                            st.metric("Forecast", f"${model_data.get('forecast', model_data.get('prediction', 0)):.2f}")
                            st.metric("Confidence", f"{model_data.get('confidence', 0)*100:.1f}%")
                            
                            # Show model-specific info
                            if model_name == 'arima':
                                st.caption(f"Model: {model_data.get('model', 'ARIMA')}")
                            elif model_name == 'lstm':
                                st.caption("Deep Learning Model")
                            elif model_name == 'monte_carlo':
                                st.caption(f"Volatility: {model_data.get('volatility', 0)*100:.1f}%")
                            else:
                                st.caption("Statistical Model")
            else:
                st.error("Model comparison data not available")
        
            # Technical Indicators
            st.markdown("---")
            st.header("📊 Advanced Technical Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                rsi_val = forecast.get('rsi', 50)
                rsi_signal = forecast.get('rsi_signal', 'NEUTRAL')
                st.metric("RSI", f"{rsi_val:.1f}", delta=rsi_signal)
                st.caption("Momentum Oscillator")
            with col2:
                macd_signal = forecast.get('macd_signal', 'NEUTRAL')
                st.metric("MACD Signal", macd_signal)
                st.caption("Trend Following")
            with col3:
                bollinger_pos = forecast.get('bollinger_position', 'MIDDLE')
                st.metric("Bollinger Position", bollinger_pos)
                st.caption("Volatility Indicator")
            with col4:
                stoch_signal = forecast.get('stochastic_signal', 'NEUTRAL')
                st.metric("Stochastic", stoch_signal)
                st.caption("Overbought/Oversold")
        
            # Prediction Charts
            st.markdown("---")
            st.header("📉 Price Forecast Visualization")
            
            # Check if we have the required data for charts
            historical_data = stock_data.get('historical')
            ensemble_data = forecast.get('ensemble', {})
            ensemble_predictions = ensemble_data.get('predictions', [])
            
            if historical_data is not None and ensemble_predictions:
                # Create forecast chart
                historical = historical_data.copy()
                
                # Get dates
                last_date = pd.to_datetime(historical.index[-1])
                future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=prediction_days, freq='D')
                
                # Create figure
                fig = go.Figure()
                
                # Add historical data
                fig.add_trace(go.Scatter(
                    x=historical.index,
                    y=historical['close'],
                    name='Historical Price',
                    line=dict(color='blue', width=2)
                ))
                
                # Add Ensemble forecast
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=ensemble_predictions,
                    name='Ensemble Forecast',
                    line=dict(color='green', width=3, dash='solid')
                ))
                
                # Add confidence bands
                ensemble_std = np.std(ensemble_predictions)
                upper_band = np.array(ensemble_predictions) + ensemble_std
                lower_band = np.array(ensemble_predictions) - ensemble_std
                
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=upper_band,
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    name='Upper Confidence'
                ))
                
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=lower_band,
                    mode='lines',
                    line=dict(width=0),
                    fillcolor='rgba(0, 255, 0, 0.2)',
                    fill='tonexty',
                    showlegend=False,
                    name='Confidence Band'
                ))
                
                fig.update_layout(
                    title=f"{stock_data.get('name', 'Stock')} Price Forecast ({prediction_days} days) - Ensemble Model",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Historical data or prediction data not available for chart visualization")
        
            # Trading Signals Dashboard
            st.markdown("---")
            st.header("📡 Trading Signals Dashboard")
            
            signal_col1, signal_col2, signal_col3 = st.columns(3)
            
            # Buy Signal
            with signal_col1:
                recommendation = forecast.get('recommendation', 'HOLD')
                avg_change = forecast.get('average_change_percent', 0)
                if recommendation in ['BUY', 'STRONG BUY']:
                    st.success(f"🟢 {recommendation} SIGNAL")
                    st.caption(f"Expected gain: {avg_change:.1f}%")
                else:
                    st.info("🟡 NO BUY SIGNAL")
                    st.caption("Wait for better entry point")
            
            # Hold Signal
            with signal_col2:
                trend_strength = trend.get('strength', 0)
                trend_direction = trend.get('direction', 'neutral')
                if recommendation == 'HOLD':
                    st.warning("🟡 HOLD SIGNAL")
                    st.caption("Trend unclear, wait for confirmation")
                elif trend_strength < 0.3:
                    st.warning("🟡 WEAK TREND")
                    st.caption("Low confidence in direction")
                else:
                    st.info("🔄 MONITOR")
                    st.caption(f"Trend: {trend_direction}")
            
            # Sell Signal
            with signal_col3:
                if recommendation in ['SELL', 'STRONG SELL']:
                    st.error(f"🔴 {recommendation} SIGNAL")
                    st.caption(f"Expected loss: {avg_change:.1f}%")
                else:
                    st.info("🟡 NO SELL SIGNAL")
                    st.caption("Price action positive")

st.markdown("---")
st.info("💡 Statistical predictions are based on historical price patterns and technical analysis. Always do your own research and consider multiple factors before making investment decisions.")
