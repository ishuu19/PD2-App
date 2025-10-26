"""Constants and Configuration"""

# 20 Well-known US Stocks (better Alpha Vantage support)
HK_STOCKS = [
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "GOOGL", # Alphabet Inc.
    "AMZN",  # Amazon.com Inc.
    "TSLA",  # Tesla Inc.
    "META",  # Meta Platforms Inc.
    "NVDA",  # NVIDIA Corporation
    "JPM",   # JPMorgan Chase & Co.
    "V",     # Visa Inc.
    "JNJ",   # Johnson & Johnson
    "WMT",   # Walmart Inc.
    "PG",    # Procter & Gamble
    "MA",    # Mastercard Inc.
    "DIS",   # The Walt Disney Company
    "BAC",   # Bank of America
    "XOM",   # Exxon Mobil Corporation
    "HD",    # The Home Depot
    "UNH",   # UnitedHealth Group
    "KO",    # The Coca-Cola Company
    "PFE",   # Pfizer Inc.
]

STOCK_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "JNJ": "Johnson & Johnson",
    "WMT": "Walmart Inc.",
    "PG": "Procter & Gamble",
    "MA": "Mastercard Inc.",
    "DIS": "The Walt Disney Company",
    "BAC": "Bank of America",
    "XOM": "Exxon Mobil Corporation",
    "HD": "The Home Depot",
    "UNH": "UnitedHealth Group",
    "KO": "The Coca-Cola Company",
    "PFE": "Pfizer Inc.",
}

# Mock Trading Settings
INITIAL_CASH = 1000000  # 1M USD

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
