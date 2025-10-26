"""Email Alerts Management"""
import streamlit as st
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
import services.ai_service as ai_service

if not auth.is_logged_in():
    st.error("Please login to manage alerts")
    st.stop()

st.title("🔔 Intelligent Email Alerts")

user_id = auth.get_user_id()

# Get stocks data
if 'stocks_data' not in st.session_state or st.session_state.stocks_data is None:
    with st.spinner("Loading stock data..."):
        st.session_state.stocks_data = stock_service.get_all_stocks()

all_stocks_data = st.session_state.stocks_data

# Alert Criteria Options
ALERT_CRITERIA = [
    "Price above threshold",
    "Price below threshold",
    "Daily % change > X%",
    "Daily % change < -X%",
    "Weekly % change > X%",
    "Monthly % change > X%",
    "Volume spike (> 2x average)",
    "RSI overbought (> 70)",
    "RSI oversold (< 30)",
    "MACD bullish crossover",
    "MACD bearish crossover",
    "Moving average golden cross",
    "Moving average death cross",
    "Bollinger band upper break",
    "Bollinger band lower break",
    "Portfolio value milestone"
]

# Create New Alert
st.header("Create New Alert")
tickers = [ticker for ticker, data in all_stocks_data.items() if data]

col1, col2 = st.columns(2)

with col1:
    selected_ticker = st.selectbox("Stock", tickers)
    alert_criteria = st.selectbox("Alert Criteria", ALERT_CRITERIA)

with col2:
    threshold = st.number_input("Threshold Value", value=100.0, step=0.01)
    email_address = st.text_input("Email Address", value=db.get_user(user_id).get('email', ''))

if st.button("📧 Create Alert", type="primary"):
    if selected_ticker and alert_criteria and threshold and email_address:
        alert_id = db.create_alert(user_id, selected_ticker, alert_criteria, threshold)
        if alert_id:
            st.success("Alert created successfully!")
        else:
            st.error("Failed to create alert")
    else:
        st.warning("Please fill in all fields")

# Existing Alerts
st.header("Your Alerts")
alerts = db.get_alerts(user_id, active_only=False)

if alerts:
    for alert in alerts:
        with st.expander(f"{alert['ticker']} - {alert['criteria']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Stock**: {alert['ticker']}")
                st.write(f"**Criteria**: {alert['criteria']}")
                st.write(f"**Threshold**: {alert['threshold']}")
            
            with col2:
                status = "Active" if alert['active'] else "Inactive"
                st.write(f"**Status**: {status}")
                st.write(f"**Created**: {alert['created_at'].strftime('%Y-%m-%d')}")
            
            with col3:
                if alert['active']:
                    if st.button("Deactivate", key=f"deactivate_{alert['_id']}"):
                        db.update_alert(str(alert['_id']), {'active': False})
                        st.rerun()
                else:
                    if st.button("Activate", key=f"activate_{alert['_id']}"):
                        db.update_alert(str(alert['_id']), {'active': True})
                        st.rerun()
                
                if st.button("Delete", key=f"delete_{alert['_id']}"):
                    db.delete_alert(str(alert['_id']))
                    st.rerun()
else:
    st.info("No alerts configured. Create one above!")

# AI Email Preview
st.header("AI Email Preview")

if alerts:
    preview_alert = st.selectbox("Select Alert to Preview", alerts, format_func=lambda x: f"{x['ticker']} - {x['criteria']}")
    
    if st.button("Generate Email Preview", type="primary"):
        if preview_alert and selected_ticker in all_stocks_data:
            stock_data = all_stocks_data[selected_ticker]
            
            alert_details = {
                'threshold': preview_alert['threshold'],
                'current_value': stock_data['current_price'],
                'change': stock_data['change_percent']
            }
            
            with st.spinner("Generating AI email..."):
                email_content = ai_service.generate_email_content(
                    preview_alert['criteria'],
                    stock_data,
                    alert_details
                )
                
                st.markdown("### Generated Email")
                st.markdown(email_content)
                
                st.markdown("---")
                st.caption("This is a preview. Actual emails will be sent when alerts trigger.")

# Alert Statistics
st.header("Alert Statistics")
active_alerts = len([a for a in alerts if a['active']])
st.metric("Active Alerts", active_alerts)
st.metric("Total Alerts", len(alerts))

st.info("💡 AI-generated emails provide context, actionable insights, and risk warnings.")
