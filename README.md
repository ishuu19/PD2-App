# Portfolio Management Platform

A comprehensive financial portfolio management platform for non-professional investors built with Streamlit, featuring AI-powered insights, real-time stock tracking, and intelligent alerts.

## Features

### 🔐 Authentication System
- User registration and login
- Secure password hashing
- Session management

### 📊 Portfolio Dashboard (Main Feature)
- Display 20 pre-selected Hong Kong stocks with comprehensive metrics
- Mock trading with 1M HKD virtual money
- Real-time portfolio tracking
- Buy/Sell functionality
- Transaction history
- Portfolio performance metrics
- AI-powered investment recommendations

### 🔮 AI Price Predictions
- Dual strategy prediction system
- PowerBI-style dashboard
- Pattern recognition
- Future price forecasts (7-day, 30-day, 90-day)
- Trading signals

### 🔔 Intelligent Email Alerts
- 12+ alert criteria
- GPT-4 powered email generation
- Price, volume, technical indicator alerts
- Portfolio value milestones

### 📈 Market Intelligence
- Multi-source news aggregation
- AI sentiment analysis
- Sector analysis
- Risk metrics (Sharpe, Sortino, VaR)
- Correlation analysis
- Market commentary

## Tech Stack

- **Frontend/Backend**: Streamlit
- **Database**: MongoDB Atlas
- **Data Source**: Yahoo Finance (yfinance)
- **AI**: OpenAI GPT-4 Turbo
- **Charts**: Plotly
- **Email**: SMTP (Gmail/SendGrid)

## Installation

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- OpenAI API key
- (Optional) Gmail/SendGrid for email alerts

### Setup

1. Clone the repository:
```bash
cd "G:/University/HKBU/Courses/COMP4145/Project Management/PD2 App"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:

Create a `.streamlit/secrets.toml` file:
```toml
MONGODB_URI = "your_mongodb_atlas_connection_string"
OPENAI_API_KEY = "your_openai_api_key"
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
```

Or set environment variables:
```bash
export MONGODB_URI="your_mongodb_atlas_connection_string"
export OPENAI_API_KEY="your_openai_api_key"
export EMAIL_USER="your_email@gmail.com"
export EMAIL_PASSWORD="your_app_password"
```

4. Run the application:
```bash
streamlit run app.py
```

## Configuration

### MongoDB Atlas Setup

1. Create a MongoDB Atlas account
2. Create a new cluster
3. Get your connection string
4. Whitelist your IP address (or 0.0.0.0/0 for Streamlit Cloud)

### OpenAI API Setup

1. Create an OpenAI account
2. Get your API key from https://platform.openai.com/api-keys
3. Add credits to your account

### Email Setup (Optional)

For Gmail:
1. Enable 2-factor authentication
2. Generate an app password
3. Use the app password in secrets

## Project Structure

```
PD2 App/
├── app.py                          # Main application
├── requirements.txt                # Dependencies
├── README.md                       # This file
├── config/
│   ├── api_keys.py                # API key management
│   └── constants.py               # Constants and configuration
├── database/
│   ├── connection.py              # MongoDB connection
│   └── models.py                  # Database models and CRUD
├── services/
│   ├── stock_data.py              # Yahoo Finance data fetching
│   ├── portfolio_service.py       # Portfolio calculations
│   ├── ai_service.py              # OpenAI GPT-4 integration
│   └── ...                        # Other services
├── utils/
│   ├── auth.py                    # Authentication helpers
│   ├── charts.py                  # Plotly charts
│   └── helpers.py                 # Utility functions
└── pages/
    ├── 1_📊_Portfolio_Dashboard.py
    ├── 2_🔮_AI_Predictions.py
    ├── 3_🔔_Email_Alerts.py
    └── 4_📈_Market_Intelligence.py
```

## Usage

1. **Register/Login**: Create an account or login
2. **View Stocks**: Browse 20 pre-selected Hong Kong stocks with metrics
3. **Trade**: Buy/sell stocks with your 1M HKD virtual money
4. **Get AI Recommendations**: Use GPT-4 for investment advice
5. **Set Alerts**: Create intelligent email alerts
6. **Track Performance**: Monitor portfolio performance in real-time

## API Rate Limiting

The application implements several strategies to avoid API rate limits:

- **Caching**: All data is cached in MongoDB (24 hours for stock data, 1 hour for AI responses)
- **Session State**: In-memory caching during session
- **Rate Limiting**: Max 2 requests/second to Yahoo Finance
- **Batch Fetching**: Fetch all 20 stocks once per session
- **Retry Logic**: Exponential backoff for failed requests

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect your repository
4. Add secrets in Streamlit Cloud dashboard
5. Deploy!

### Local Deployment

```bash
streamlit run app.py --server.port=8501
```

## Troubleshooting

### MongoDB Connection Issues
- Check your connection string
- Ensure IP is whitelisted
- Verify credentials

### API Rate Limiting
- Wait a few minutes
- Refresh stock data manually
- Check cached data is being used

### OpenAI API Errors
- Verify API key is correct
- Check account has credits
- Review rate limits

## License

This project is developed for educational purposes.

## Authors

Financial Software Development Team - HKBU COMP4145 Project Management Course
