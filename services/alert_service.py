"""Email Alert Service using Gmail SMTP"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config.api_keys as keys
import services.ai_service as ai_service
import services.stock_data as stock_data

def send_alert_email(user_email: str, ticker: str, criteria: str, threshold: float, 
                    stock_data_dict: dict, alert_details: dict = None) -> bool:
    """Send alert email using Gmail SMTP"""
    
    try:
        # Get Gmail credentials and SMTP config
        gmail_user, gmail_password = keys.get_gmail_credentials()
        smtp_config = keys.get_gmail_smtp_config()
        
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
        .stock-card {{ background: white; padding: 20px; margin: 15px 0; 
                      border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .alert-badge {{ background: #ff4444; color: white; padding: 8px 16px; 
                       border-radius: 20px; display: inline-block; 
                       margin-bottom: 15px; font-weight: bold; }}
        .stock-name {{ font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px; }}
        .current-price {{ font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; 
                 margin-top: 20px; }}
        .stat {{ background: #f8f9fa; padding: 15px; text-align: center; 
                border-radius: 8px; border: 1px solid #e9ecef; }}
        .stat-value {{ font-size: 18px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; 
                  font-size: 12px; }}
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
            
            <div class="stock-card">
                <div class="stock-name">{stock_data_dict.get('name', '')} ({ticker})</div>
                <div class="current-price">${stock_data_dict.get('current_price', 'N/A'):.2f}</div>
                
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
        </div>
        
        <div class="footer">
            <p>This is an automated alert from Investor's COMP4145.</p>
            <p>Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = user_email
        msg['Subject'] = f"🚨 Alert: {stock_data_dict.get('name', ticker)} - {criteria.replace('_', ' ').title()}"
        
        # Create plain text version
        text_content = f"""
Hi {user_email.split('@')[0]},

We are sending you the alert set by you in Investor's COMP4145.

Stock Alert Triggered
Your portfolio alert has been activated

⚠️ ALERT ACTIVE
Alert Criteria: {criteria.replace('_', ' ').title()}
Threshold: {threshold}

{stock_data_dict.get('name', '')} ({ticker})
Current Price: ${stock_data_dict.get('current_price', 'N/A'):.2f}

{stock_data_dict.get('change_percent', 0):.2f}% Daily Change
{stock_data_dict.get('volume', 0):,} Volume
{stock_data_dict.get('pe_ratio', 'N/A')} P/E Ratio
{stock_data_dict.get('beta', 'N/A')} Beta

Hope this helps

Best regards,
The Investor's Team
"""
        
        # Attach parts
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email via Gmail SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            if smtp_config['use_tls']:
                server.starttls(context=context)
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        
        return True
            
    except Exception as e:
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
        'Price above threshold': lambda data, t: data.get('current_price', 0) > t,
        'Price below threshold': lambda data, t: data.get('current_price', 0) < t,
        'Daily % change > X%': lambda data, t: data.get('change_percent', 0) > t,
        'Daily % change < -X%': lambda data, t: data.get('change_percent', 0) < -t,
        'Weekly % change > X%': lambda data, t: data.get('returns_1m', 0) > t,
        'Monthly % change > X%': lambda data, t: data.get('returns_3m', 0) > t,
        'Volume spike (> 2x average)': lambda data, t: data.get('volume', 0) > t,
        'RSI overbought (> 70)': lambda data, t: data.get('rsi', 50) > t,
        'RSI oversold (< 30)': lambda data, t: data.get('rsi', 50) < t,
        'MACD bullish crossover': lambda data, t: data.get('macd', 0) > 0,
        'MACD bearish crossover': lambda data, t: data.get('macd', 0) < 0,
        'Moving average golden cross': lambda data, t: data.get('ma_golden_cross', False),
        'Moving average death cross': lambda data, t: data.get('ma_death_cross', False),
        'Bollinger band upper break': lambda data, t: data.get('bb_upper_break', False),
        'Bollinger band lower break': lambda data, t: data.get('bb_lower_break', False),
        'Portfolio value milestone': lambda data, t: data.get('portfolio_value', 0) > t,
    }
    
    check_func = criteria_map.get(criteria)
    if check_func:
        return check_func(stock_data, threshold)
    
    return False
