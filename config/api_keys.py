"""API Key Management - Reads from Streamlit secrets and environment variables"""
import streamlit as st
import os
from typing import Optional

def get_mongodb_uri() -> Optional[str]:
    """Get MongoDB URI from secrets or environment"""
    try:
        if hasattr(st, 'secrets') and 'MONGODB_URI' in st.secrets:
            return st.secrets['MONGODB_URI']
    except:
        pass
    return os.getenv('MONGODB_URI')

def get_genai_api_key() -> Optional[str]:
    """Get HKBU GenAI API key from secrets or environment"""
    try:
        if hasattr(st, 'secrets') and 'GENAI_API_KEY' in st.secrets:
            return st.secrets['GENAI_API_KEY']
    except:
        pass
    return os.getenv('GENAI_API_KEY')

def get_genai_endpoint() -> Optional[str]:
    """Get HKBU GenAI endpoint from secrets or environment"""
    try:
        if hasattr(st, 'secrets') and 'GENAI_ENDPOINT' in st.secrets:
            return st.secrets['GENAI_ENDPOINT']
    except:
        pass
    return os.getenv('GENAI_ENDPOINT', 'https://genai.hkbu.edu.hk/api/v0/rest')

def get_genai_model() -> str:
    """Get the model deployment name"""
    try:
        if hasattr(st, 'secrets') and 'GENAI_MODEL' in st.secrets:
            return st.secrets['GENAI_MODEL']
    except:
        pass
    return os.getenv('GENAI_MODEL', 'gpt-4')

def get_resend_api_key() -> Optional[str]:
    """Get Resend API key from secrets or environment"""
    try:
        if hasattr(st, 'secrets') and 'RESEND_API_KEY' in st.secrets:
            return st.secrets['RESEND_API_KEY']
    except:
        pass
    return os.getenv('RESEND_API_KEY')

def get_email_from() -> str:
    """Get email from address"""
    try:
        if hasattr(st, 'secrets') and 'EMAIL_FROM' in st.secrets:
            return st.secrets['EMAIL_FROM']
    except:
        pass
    return os.getenv('EMAIL_FROM', 'onboarding@resend.dev')

# Finnhub API Functions (replacing Alpha Vantage)
def get_finnhub_api_keys() -> list[str]:
    """Get list of Finnhub API keys"""
    # Default keys provided by user
    default_keys = [
        'd3umblhr01qil4aqpgj0d3umblhr01qil4aqpgjg',
        'd3vo1thr01qhm1te7m50d3vo1thr01qhm1te7m5g',
        'd3vo27hr01qhm1te7nogd3vo27hr01qhm1te7np0',
        'd3vo2gpr01qhm1te7p30d3vo2gpr01qhm1te7p3g',
        'd3vo34hr01qhm1te7ru0d3vo34hr01qhm1te7rug',
        'd3vo3b1r01qhm1te7sugd3vo3b1r01qhm1te7sv0',
        'd3vo3gpr01qhm1te7tngd3vo3gpr01qhm1te7to0',
        'd3vo3l9r01qhm1te7ub0d3vo3l9r01qhm1te7ubg',
        'd3vo3r1r01qhm1te7v8gd3vo3r1r01qhm1te7v90',
        'd3vo40pr01qhm1te8030d3vo40pr01qhm1te803g'
    ]
    
    try:
        if hasattr(st, 'secrets') and 'FINNHUB_KEYS' in st.secrets:
            keys = st.secrets['FINNHUB_KEYS']
            if isinstance(keys, list) and len(keys) > 0:
                return keys
        elif hasattr(st, 'secrets') and 'FINNHUB_API_KEY' in st.secrets:
            return [st.secrets['FINNHUB_API_KEY']]
    except:
        pass
    
    # Check environment variables
    env_keys = os.getenv('FINNHUB_KEYS')
    if env_keys:
        return env_keys.split(',')
    
    env_key = os.getenv('FINNHUB_API_KEY')
    if env_key:
        return [env_key]
    
    # Return default keys
    return default_keys

def get_email_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get email credentials from secrets or environment"""
    try:
        if hasattr(st, 'secrets'):
            user = st.secrets.get('EMAIL_USER') or os.getenv('EMAIL_USER')
            password = st.secrets.get('EMAIL_PASSWORD') or os.getenv('EMAIL_PASSWORD')
            return user, password
    except:
        pass
    return os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD')

def get_gmail_credentials() -> tuple[str, str]:
    """Get Gmail credentials - using hardcoded values for demo"""
    return "iammistermiss@gmail.com", "yeme nxvn wrrt leto"

def get_gmail_smtp_config() -> dict:
    """Get Gmail SMTP configuration"""
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True
    }

def validate_keys() -> dict[str, bool]:
    """Validate all required API keys are present"""
    return {
        'mongodb': get_mongodb_uri() is not None,
        'genai': get_genai_api_key() is not None,
        'finnhub': len(get_finnhub_api_keys()) > 0,
        'resend': get_resend_api_key() is not None
    }
