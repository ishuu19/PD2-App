"""Email Alert Service using Resend API"""
import requests
import config.api_keys as keys
import services.ai_service as ai_service
import services.stock_data as stock_data

def send_alert_email(user_email: str, ticker: str, criteria: str, threshold: float, 
                    stock_data_dict: dict, alert_details: dict = None) -> bool:
    """Send alert email using Resend API"""
    
    resend_key = keys.get_resend_api_key()
    email_from = keys.get_email_from()
    
    if not resend_key:
        return False
    
    try:
        # Generate AI email content
        email_content = ai_service.generate_email_content(
            criteria, stock_data_dict, alert_details or {}
        )
        
        # Create email HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .stock-info {{ background: white; padding: 15px; margin: 15px 0; 
                      border-left: 4px solid #667eea; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; 
                 margin-top: 15px; }}
        .stat {{ background: white; padding: 10px; text-align: center; 
                border-radius: 5px; }}
        .stat-value {{ font-size: 20px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; 
                  font-size: 12px; }}
        .alert-badge {{ background: #ff4444; color: white; padding: 5px 15px; 
                       border-radius: 20px; display: inline-block; 
                       margin-bottom: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Stock Alert Triggered</h1>
            <p>Your portfolio alert has been activated</p>
        </div>
        
        <div class="content">
            <div class="alert-badge">⚠️ ALERT ACTIVE</div>
            <p><strong>Alert Criteria:</strong> {criteria.replace('_', ' ').title()}</p>
            <p><strong>Threshold:</strong> {threshold}</p>
            
            <div class="stock-info">
                <h2>{stock_data_dict.get('name', '')} ({ticker})</h2>
                <p style="font-size: 24px; font-weight: bold; color: #667eea;">
                    Current Price: ${stock_data_dict.get('current_price', 'N/A'):.2f}
                </p>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{stock_data_dict.get('change_percent', 0):.2f}%</div>
                        <div class="stat-label">Daily Change</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stock_data_dict.get('volume', 0):,}</div>
                        <div class="stat-label">Volume</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stock_data_dict.get('pe_ratio', 'N/A')}</div>
                        <div class="stat-label">P/E Ratio</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stock_data_dict.get('beta', 'N/A')}</div>
                        <div class="stat-label">Beta</div>
                    </div>
                </div>
            </div>
            
            <div style="background: white; padding: 15px; margin-top: 15px;">
                <h3>AI Analysis</h3>
                <p>{email_content.replace(chr(10), '<br>')}</p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #ddd;">
                <p><strong>Action Required:</strong> Review this stock's performance and decide if you want to take any action on your portfolio.</p>
            </div>
        </div>
        
        <div class="footer">
            <p>This is an automated alert from your Portfolio Management Platform.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Send email via Resend API
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": email_from,
            "to": user_email,
            "subject": f"🚨 Alert: {stock_data_dict.get('name', ticker)} - {criteria.replace('_', ' ').title()}",
            "html": html_content
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Resend API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending alert email: {str(e)}")
        return False


def check_alerts(user_id: str, user_email: str):
    """Check all active alerts and send emails if triggered"""
    import database.models as db
    
    alerts = db.get_alerts(user_id, active_only=True)
    
    for alert in alerts:
        ticker = alert['ticker']
        criteria = alert['criteria']
        threshold = alert['threshold']
        
        # Get current stock data
        stock_data_dict = stock_data.get_stock_data(ticker)
        
        if not stock_data_dict:
            continue
        
        # Check if alert should trigger
        triggered = check_alert_criteria(stock_data_dict, criteria, threshold)
        
        if triggered:
            # Send email
            send_alert_email(user_email, ticker, criteria, threshold, stock_data_dict)
            
            # Update alert last triggered
            db.update_alert_last_triggered(str(alert['_id']))


def check_alert_criteria(stock_data: dict, criteria: str, threshold: float) -> bool:
    """Check if alert criteria is met"""
    
    criteria_map = {
        'price_above': lambda data, t: data.get('current_price', 0) > t,
        'price_below': lambda data, t: data.get('current_price', 0) < t,
        'percent_change_daily': lambda data, t: abs(data.get('change_percent', 0)) > t,
        'volume_spike': lambda data, t: data.get('volume', 0) > t,
        'rsi_overbought': lambda data, t: data.get('rsi', 50) > t,
        'rsi_oversold': lambda data, t: data.get('rsi', 50) < t,
    }
    
    check_func = criteria_map.get(criteria)
    if check_func:
        return check_func(stock_data, threshold)
    
    return False
