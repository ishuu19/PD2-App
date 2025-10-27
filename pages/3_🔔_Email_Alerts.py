"""Email Alerts Management"""
import streamlit as st
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
import services.ai_service as ai_service
import services.scheduler_service as scheduler_service

if not auth.is_logged_in():
    st.error("Please login to manage alerts")
    st.stop()

st.title("🔔 Intelligent Email Alerts")

# Scheduler Status
st.header("🤖 Automated System Status")
scheduler_status = scheduler_service.get_scheduler_status()

col1, col2, col3 = st.columns(3)
with col1:
    status_icon = "🟢" if scheduler_status['running'] else "🔴"
    st.metric("Scheduler Status", "Running" if scheduler_status['running'] else "Stopped", 
              delta=None, help="Automated daily tasks at 12:00 AM")
    
with col2:
    next_run = scheduler_status['next_run']
    if next_run:
        st.metric("Next Run", next_run.strftime("%H:%M"), 
                  delta=None, help="Next scheduled execution")
    else:
        st.metric("Next Run", "Not scheduled", delta=None)
        
with col3:
    st.metric("Active Jobs", scheduler_status['jobs_count'], 
              delta=None, help="Number of scheduled tasks")

if scheduler_status['running']:
    st.success("✅ Automated system is running - Alerts will be checked daily at 12:00 AM")
else:
    st.warning("⚠️ Automated system is not running")

user_id = auth.get_user_id()

# Get stocks data (loaded from yfinance)
all_stocks_data = stock_service.get_all_stocks()

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
    with st.spinner("📧 Creating alert..."):
        try:
            if selected_ticker and alert_criteria and threshold and email_address:
                alert_id = db.create_alert(user_id, selected_ticker, alert_criteria, threshold)
                if alert_id:
                    st.success("Alert created successfully!")
                else:
                    st.error("Failed to create alert")
            else:
                st.warning("Please fill in all fields")
        except Exception as e:
            st.error(f"Error creating alert: {str(e)}")

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
                        with st.spinner("Deactivating alert..."):
                            try:
                                db.update_alert(str(alert['_id']), {'active': False})
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deactivating alert: {str(e)}")
                else:
                    if st.button("Activate", key=f"activate_{alert['_id']}"):
                        with st.spinner("Activating alert..."):
                            try:
                                db.update_alert(str(alert['_id']), {'active': True})
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error activating alert: {str(e)}")
                
                if st.button("Delete", key=f"delete_{alert['_id']}"):
                    with st.spinner("Deleting alert..."):
                        try:
                            db.delete_alert(str(alert['_id']))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting alert: {str(e)}")
else:
    st.info("No alerts configured. Create one above!")

# Demo Email Testing
st.header("📧 Demo Email Testing")

if alerts:
    demo_alert = st.selectbox("Select Alert for Demo", alerts, format_func=lambda x: f"{x['ticker']} - {x['criteria']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Try Checking Emails", type="primary"):
            with st.spinner("🔍 Checking alerts and simulating email triggers..."):
                try:
                    import services.alert_service as alert_service
                    user_email = db.get_user(user_id).get('email', '')
                    
                    if not user_email:
                        st.error("No email address found for user. Please update your profile.")
                    else:
                        # Simulate checking alerts
                        active_alerts = [a for a in alerts if a['active']]
                        st.info(f"Found {len(active_alerts)} active alerts to check...")
                        
                        # Check each alert
                        triggered_count = 0
                        for alert in active_alerts:
                            ticker = alert['ticker']
                            if ticker in all_stocks_data:
                                stock_data = all_stocks_data[ticker]
                                criteria = alert['criteria']
                                threshold = alert['threshold']
                                
                                # Check if alert would trigger
                                triggered = alert_service.check_alert_criteria(stock_data, criteria, threshold)
                                if triggered:
                                    triggered_count += 1
                                    st.success(f"✅ {ticker} - {criteria} would trigger! (Current: ${stock_data['current_price']:.2f}, Threshold: ${threshold:.2f})")
                                else:
                                    st.info(f"ℹ️ {ticker} - {criteria} not triggered (Current: ${stock_data['current_price']:.2f}, Threshold: ${threshold:.2f})")
                        
                        if triggered_count > 0:
                            st.success(f"🎉 {triggered_count} alert(s) would trigger and send emails!")
                        else:
                            st.info("No alerts would trigger at this time.")
                            
                except Exception as e:
                    st.error(f"Error checking alerts: {str(e)}")
    
    with col2:
        if st.button("📤 Send Demo Email", type="secondary"):
            with st.spinner("📤 Sending demo email..."):
                try:
                    import services.alert_service as alert_service
                    user_email = db.get_user(user_id).get('email', '')
                    
                    if not user_email:
                        st.error("No email address found for user. Please update your profile.")
                    else:
                        if demo_alert and demo_alert['ticker'] in all_stocks_data:
                            stock_data = all_stocks_data[demo_alert['ticker']]
                            
                            # Send demo email
                            success = alert_service.send_alert_email(
                                user_email,
                                demo_alert['ticker'],
                                demo_alert['criteria'],
                                demo_alert['threshold'],
                                stock_data,
                                {
                                    'threshold': demo_alert['threshold'],
                                    'current_value': stock_data['current_price'],
                                    'change': stock_data['change_percent']
                                }
                            )
                            
                            if success:
                                st.success(f"✅ Demo email sent successfully to {user_email}!")
                                st.info("Check your inbox for the demo alert email.")
                            else:
                                st.error("Failed to send demo email. Please check your email configuration.")
                        else:
                            st.warning("Please select a valid alert for demo.")
                            
                except Exception as e:
                    st.error(f"Error sending demo email: {str(e)}")

# Manual Alert Testing
st.header("🔧 Manual Alert Testing")
st.info("Use this section to manually test the automated alert system without waiting for 12:00 AM")

if st.button("🚀 Run Manual Alert Check", type="primary"):
    with st.spinner("🔍 Running manual alert check for all users..."):
        try:
            scheduler_service.run_manual_alert_check()
            st.success("✅ Manual alert check completed! Check the console for detailed results.")
        except Exception as e:
            st.error(f"Error running manual alert check: {str(e)}")

else:
    st.info("Create some alerts first to test email functionality!")

# Alert Statistics
st.header("Alert Statistics")
active_alerts = len([a for a in alerts if a['active']])
st.metric("Active Alerts", active_alerts)
st.metric("Total Alerts", len(alerts))

st.info("💡 AI-generated emails provide context, actionable insights, and risk warnings.")
