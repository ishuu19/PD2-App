"""Constants and Configuration"""

# 20 Pre-selected Hong Kong Stocks
HK_STOCKS = [
    "0700.HK",  # Tencent Holdings
    "0005.HK",  # HSBC Holdings
    "0941.HK",  # China Mobile
    "0388.HK",  # Hong Kong Exchanges
    "1299.HK",  # AIA Group
    "2318.HK",  # Ping An Insurance
    "1398.HK",  # Industrial and Commercial Bank of China
    "3988.HK",  # Bank of China
    "0939.HK",  # China Construction Bank
    "1024.HK",  # Kuaishou Technology
    "3690.HK",  # Meituan
    "9988.HK",  # Alibaba Group
    "1810.HK",  # Xiaomi Corporation
    "2388.HK",  # BOC Hong Kong Holdings
    "2899.HK",  # Zijin Mining
    "2269.HK",  # Midea Group
    "2628.HK",  # China Life Insurance
    "3328.HK",  # Bank of Communications
    "1378.HK",  # China Hongqiao Group
    "2330.HK",  # Power Assets Holdings
]

STOCK_NAMES = {
    "0700.HK": "Tencent Holdings",
    "0005.HK": "HSBC Holdings",
    "0941.HK": "China Mobile",
    "0388.HK": "Hong Kong Exchanges",
    "1299.HK": "AIA Group",
    "2318.HK": "Ping An Insurance",
    "1398.HK": "ICBC",
    "3988.HK": "Bank of China",
    "0939.HK": "China Construction Bank",
    "1024.HK": "Kuaishou Technology",
    "3690.HK": "Meituan",
    "9988.HK": "Alibaba Group",
    "1810.HK": "Xiaomi Corporation",
    "2388.HK": "BOC Hong Kong Holdings",
    "2899.HK": "Zijin Mining",
    "2269.HK": "Midea Group",
    "2628.HK": "China Life Insurance",
    "3328.HK": "Bank of Communications",
    "1378.HK": "China Hongqiao Group",
    "2330.HK": "Power Assets Holdings",
}

# Mock Trading Settings
INITIAL_CASH = 1000000  # 1M HKD

# Data Refresh Settings
STOCK_DATA_TTL = 3600  # 1 hour in seconds
PRICE_REFRESH_INTERVAL = 300  # 5 minutes
CACHE_TTL = 86400  # 24 hours for MongoDB cache
AI_CACHE_TTL = 3600  # 1 hour for AI responses

# Alert Criteria Types
ALERT_CRITERIA = [
    "price_above",
    "price_below",
    "percent_change_daily",
    "percent_change_weekly",
    "percent_change_monthly",
    "volume_spike",
    "rsi_overbought",
    "rsi_oversold",
    "macd_crossover_bullish",
    "macd_crossover_bearish",
    "ma_crossover_golden",
    "ma_crossover_death",
    "bollinger_break_upper",
    "bollinger_break_lower",
    "support_resistance_break",
    "dividend_announcement",
    "earnings_date",
    "ai_sentiment_shift",
    "portfolio_value_milestone",
]

# HKBU GenAI Configuration
GENAI_MODEL = "gpt-4"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7

# Email Settings
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
MAX_EMAILS_PER_HOUR = 10
