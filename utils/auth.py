"""Authentication Helper Functions - SECURE VERSION with session-only tokens"""
import streamlit as st
import jwt
from datetime import datetime, timedelta
import os

# Secret key for JWT signing
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_secret_key_change_in_production')

# Token expiration times
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # Short-lived access token
REFRESH_TOKEN_EXPIRY = timedelta(hours=1)  # Same as access token - enforce 1 hour logout

def _generate_token(user_id: str, username: str, email: str, expiry: timedelta) -> str:
    """Generate a JWT token"""
    now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'exp': now + expiry,
        'iat': now
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def _decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def is_logged_in():
    """Check if user is logged in - session-based authentication only
    
    SECURITY: This version does NOT persist tokens in database or URL.
    Users must login for each new browser session.
    Tokens only exist in session_state during active session.
    """
    # Initialize session state if not exists
    if 'auth_initialized' not in st.session_state:
        st.session_state.auth_initialized = True
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
    
    # Check if we have valid tokens in session state
    access_token = st.session_state.get('access_token')
    if access_token:
        payload = _decode_token(access_token)
        if payload:
            # Valid access token - user is logged in
            # Ensure user info is set
            if 'user_id' not in st.session_state or st.session_state.user_id is None:
                st.session_state.user_id = payload['user_id']
                st.session_state.username = payload['username']
                st.session_state.email = payload['email']
            return True
    
    # Check refresh token in session state
    refresh_token = st.session_state.get('refresh_token')
    if refresh_token:
        payload = _decode_token(refresh_token)
        if payload:
            # Valid refresh token, generate new access token
            user_id = payload['user_id']
            username = payload['username']
            email = payload['email']
            
            new_access_token = _generate_token(user_id, username, email, ACCESS_TOKEN_EXPIRY)
            
            # Update session state
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.session_state.email = email
            st.session_state.access_token = new_access_token
            st.session_state.refresh_token = refresh_token
            
            return True
    
    # No valid authentication found
    return False

def login_user(user_id: str, username: str, email: str):
    """Set user session with access and refresh tokens
    
    SECURITY: Tokens are stored ONLY in session_state, not in database.
    When browser session ends, user must login again.
    """
    # Generate tokens (both expire after 1 hour - auto logout enforced)
    access_token = _generate_token(user_id, username, email, ACCESS_TOKEN_EXPIRY)
    refresh_token = _generate_token(user_id, username, email, REFRESH_TOKEN_EXPIRY)
    
    # Store in session state ONLY
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.email = email
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token

def logout_user():
    """Clear user session and tokens
    
    SECURITY: Only clears session_state. No database cleanup needed
    since we don't store tokens in database anymore.
    """
    # Clear session state
    keys_to_clear = ['user_id', 'username', 'email', 'access_token', 'refresh_token']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def get_user_id():
    """Get current user ID"""
    return st.session_state.get('user_id')

def get_username():
    """Get current username"""
    return st.session_state.get('username', 'Guest')

def get_email():
    """Get current user email"""
    return st.session_state.get('email', '')

def refresh_access_token():
    """Manually refresh the access token using the refresh token"""
    if 'refresh_token' in st.session_state:
        payload = _decode_token(st.session_state.refresh_token)
        if payload:
            # Generate new access token
            access_token = _generate_token(
                payload['user_id'],
                payload['username'],
                payload['email'],
                ACCESS_TOKEN_EXPIRY
            )
            st.session_state.access_token = access_token
            return True
    return False

def debug_auth_status():
    """Debug function to show current authentication status"""
    debug_info = {
        'session_state_user_id': st.session_state.get('user_id'),
        'session_state_username': st.session_state.get('username'),
        'session_state_email': st.session_state.get('email'),
        'has_access_token': 'access_token' in st.session_state and st.session_state.access_token is not None,
        'has_refresh_token': 'refresh_token' in st.session_state and st.session_state.refresh_token is not None,
        'is_logged_in': is_logged_in()
    }
    
    return debug_info
