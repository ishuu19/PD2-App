"""HKBU GenAI Service with Response Caching"""
import hashlib
import json
from typing import Optional, Dict
import requests
import config.api_keys as keys
import database.models as db
from config import constants

def get_ai_response(prompt: str, system_prompt: Optional[str] = None, 
                   max_tokens: int = constants.OPENAI_MAX_TOKENS,
                   temperature: float = constants.OPENAI_TEMPERATURE) -> Optional[str]:
    """Get AI response from HKBU GenAI API with caching"""
    # Create query hash
    query_dict = {
        'prompt': prompt,
        'system_prompt': system_prompt,
        'max_tokens': max_tokens,
        'temperature': temperature
    }
    query_hash = hashlib.md5(json.dumps(query_dict, sort_keys=True).encode()).hexdigest()
    
    # Check cache
    cached_response = db.get_cached_ai_response(query_hash)
    if cached_response:
        return cached_response
    
    # Get fresh response from HKBU GenAI API
    api_key = keys.get_genai_api_key()
    base_endpoint = keys.get_genai_endpoint()
    model_name = keys.get_genai_model()
    
    if not api_key or not base_endpoint:
        return "AI API not configured."
    
    try:
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Call HKBU GenAI API - Try multiple authentication methods
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
            "Authorization": f"Bearer {api_key}"
        }
        
        # HKBU GenAI API format - Azure OpenAI compatible
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        # Construct the correct endpoint: /openai/deployments/{modelDeploymentName}/chat/completions
        endpoint = f"{base_endpoint}/openai/deployments/{model_name}/chat/completions?api-version=v1"
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            response_json = response.json()
            result = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
            if result:
                # Cache response
                db.cache_ai_response(query_hash, result)
                return result
            else:
                return f"AI response format error: {response_json}"
        else:
            return f"Error generating AI response: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error generating AI response: {str(e)}"

def get_portfolio_recommendations(portfolio_summary: Dict) -> str:
    """Get AI portfolio recommendations"""
    system_prompt = "You are a professional financial advisor specializing in Hong Kong stocks. Provide clear, actionable investment advice."
    
    prompt = f"""
    Analyze this portfolio and provide buy/sell/hold recommendations:
    
    Cash Available: {portfolio_summary.get('cash', 0):,.0f} HKD
    Total Portfolio Value: {portfolio_summary.get('total_value', 0):,.0f} HKD
    Total Return: {portfolio_summary.get('total_return', 0):.2f}%
    
    Holdings:
    {json.dumps(portfolio_summary.get('holdings', {}), indent=2)}
    
    Provide:
    1. Top 3 stocks to BUY with reasoning
    2. Top 3 stocks to SELL (if any) with reasoning
    3. Portfolio health assessment
    4. Risk level and diversification score
    """
    
    return get_ai_response(prompt, system_prompt, max_tokens=1500)

def get_stock_analysis(stock_data: Dict) -> str:
    """Get AI stock analysis"""
    system_prompt = "You are a technical analyst specializing in stock market analysis. Provide detailed technical and fundamental analysis."
    
    prompt = f"""
    Analyze this stock and provide investment insights:
    
    Ticker: {stock_data.get('ticker')}
    Name: {stock_data.get('name')}
    Current Price: {stock_data.get('current_price')}
    Change: {stock_data.get('change_percent')}%
    P/E Ratio: {stock_data.get('pe_ratio')}
    Beta: {stock_data.get('beta')}
    Volatility: {stock_data.get('volatility')}%
    Dividend Yield: {stock_data.get('dividend_yield')}%
    Returns (1M/3M/6M/1Y): {stock_data.get('returns_1m')}% / {stock_data.get('returns_3m')}% / {stock_data.get('returns_6m')}% / {stock_data.get('returns_1y')}%
    
    Provide:
    1. Buy/Sell/Hold recommendation
    2. Key strengths and weaknesses
    3. Technical analysis summary
    4. Risk assessment
    5. Target price and price action outlook
    """
    
    return get_ai_response(prompt, system_prompt, max_tokens=1000)

def get_price_prediction(stock_data: Dict, days: int = 30) -> str:
    """Get AI price prediction"""
    system_prompt = "You are a quantitative analyst specializing in stock price forecasting using pattern recognition and technical analysis."
    
    prompt = f"""
    Predict the stock price for {stock_data.get('name')} ({stock_data.get('ticker')}) over the next {days} days.
    
    Current Price: {stock_data.get('current_price')}
    Recent Performance: {stock_data.get('returns_1m')}% (1M), {stock_data.get('returns_3m')}% (3M)
    Volatility: {stock_data.get('volatility')}%
    Beta: {stock_data.get('beta')}
    
    Consider:
    1. Current trend and momentum
    2. Technical indicators (RSI, MACD patterns)
    3. Support and resistance levels
    4. Historical volatility
    5. Beta and market correlation
    
    Provide:
    1. Price forecast (high, low, expected)
    2. Confidence level (1-10)
    3. Key factors influencing the prediction
    4. Key risks and scenarios
    """
    
    return get_ai_response(prompt, system_prompt, max_tokens=800)

def generate_email_content(alert_type: str, stock_data: Dict, alert_details: Dict) -> str:
    """Generate email content for alerts using GPT-4"""
    system_prompt = "You are a professional financial communication specialist. Write clear, actionable, and personalized email alerts."
    
    prompt = f"""
    Generate a professional email alert for a stock price notification:
    
    Stock: {stock_data.get('name')} ({stock_data.get('ticker')})
    Current Price: {stock_data.get('current_price')}
    Alert Type: {alert_type}
    Alert Details: {json.dumps(alert_details, indent=2)}
    
    Write an email that:
    1. Clearly explains why the alert was triggered
    2. Provides context about current market conditions
    3. Offers actionable next steps
    4. Includes relevant risk warnings
    5. Is professional but accessible
    
    Make it personal and helpful, not just automated.
    """
    
    return get_ai_response(prompt, system_prompt, max_tokens=1200)
