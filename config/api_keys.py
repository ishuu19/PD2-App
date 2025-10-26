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

def validate_keys() -> dict[str, bool]:
    """Validate all required API keys are present"""
    return {
        'mongodb': get_mongodb_uri() is not None,
        'genai': get_genai_api_key() is not None,
        'resend': get_resend_api_key() is not None
    }
