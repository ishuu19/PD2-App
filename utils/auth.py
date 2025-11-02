"""Authentication Helper Functions - SECURE VERSION with session-only tokens and device binding"""
import streamlit as st
import jwt
from datetime import datetime, timedelta
import os
import hashlib
import secrets
import socket

# Secret key for JWT signing
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_secret_key_change_in_production')

# Token expiration times
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # Short-lived access token
REFRESH_TOKEN_EXPIRY = timedelta(hours=1)  # Same as access token - enforce 1 hour logout

def _get_client_ip():
    """Extract client IP address from request headers
    
    SECURITY: This detects the real IP address of the user's device/network.
    Checks multiple headers in case of proxies, load balancers, etc.
    """
    try:
        # Try to get IP from various headers (handles proxies, load balancers, etc.)
        headers = st.runtime.scriptrunner.get_script_run_ctx().request_info.headers if hasattr(st.runtime, 'scriptrunner') else {}
        
        # Check various IP headers (in order of preference)
        ip_headers = [
            'X-Forwarded-For',      # Most common for reverse proxies
            'X-Real-Ip',            # Alternative header
            'CF-Connecting-Ip',     # Cloudflare
            'True-Client-Ip',       # Some CDNs
            'X-Client-Ip',          # Alternative
        ]
        
        for header in ip_headers:
            if header in headers:
                # X-Forwarded-For can have multiple IPs (client, proxy1, proxy2...)
                # Get the first one (original client)
                ip_list = headers[header].split(',')
                ip = ip_list[0].strip()
                if ip:
                    return ip
        
        # Fallback: try to get from server context
        try:
            # For localhost/development, use a default identifier
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"  # Localhost fallback
        
    except Exception as e:
        # If all else fails, return a default that will still enforce consistency
        return "unknown"

def _get_or_generate_device_id():
    """Generate a unique device ID for this browser session
    
    SECURITY: This creates a device fingerprint based on browser session.
    Each browser tab/window gets a unique device_id that persists in session_state.
    """
    # Check if device_id already exists in session
    if 'device_id' not in st.session_state or not st.session_state.device_id:
        # Generate a unique device ID based on session and some randomness
        # Combine session ID with random token for uniqueness
        session_id = st.session_state.get('session_id', secrets.token_hex(16))
        random_token = secrets.token_hex(16)
        
        # Create a hash-based device identifier
        device_fingerprint = f"{session_id}:{random_token}"
        device_id = hashlib.sha256(device_fingerprint.encode()).hexdigest()
        
        st.session_state.device_id = device_id
    
    return st.session_state.device_id

def _generate_token(user_id: str, username: str, email: str, device_id: str, client_ip: str, expiry: timedelta) -> str:
    """Generate a JWT token with device and IP binding
    
    SECURITY: Each JWT is bound to a specific device_id AND client IP address.
    Tokens from one device/IP cannot be used on another device/IP, even if someone intercepts the token.
    """
    now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'device_id': device_id,  # Device binding for security
        'client_ip': client_ip,  # IP address binding for additional security
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
    """Check if user is logged in - session-based authentication with device and IP binding
    
    SECURITY: This version does NOT persist tokens in database or URL.
    Users must login for each new browser session.
    Tokens only exist in session_state during active session.
    Each token is bound to a specific device_id AND client_ip for additional security.
    """
    # Initialize session state if not exists
    if 'auth_initialized' not in st.session_state:
        st.session_state.auth_initialized = True
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.device_id = None
        st.session_state.client_ip = None
    
    # Get current IP and device_id
    current_device_id = _get_or_generate_device_id()
    current_ip = _get_client_ip()
    
    # Check if we have valid tokens in session state
    access_token = st.session_state.get('access_token')
    if access_token:
        payload = _decode_token(access_token)
        if payload:
            # Validate device_id matches current device
            token_device_id = payload.get('device_id')
            token_client_ip = payload.get('client_ip')
            
            if token_device_id != current_device_id:
                # Device mismatch - invalidate session
                logout_user()
                return False
            
            if token_client_ip != current_ip:
                # IP mismatch - invalidate session (user changed network/location)
                logout_user()
                return False
            
            # Valid access token with matching device and IP - user is logged in
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
            # Validate device_id and IP match current device
            token_device_id = payload.get('device_id')
            token_client_ip = payload.get('client_ip')
            
            if token_device_id != current_device_id:
                # Device mismatch - invalidate session
                logout_user()
                return False
            
            if token_client_ip != current_ip:
                # IP mismatch - invalidate session
                logout_user()
                return False
            
            # Valid refresh token with matching device and IP, generate new access token
            user_id = payload['user_id']
            username = payload['username']
            email = payload['email']
            device_id = payload['device_id']
            client_ip = payload['client_ip']
            
            new_access_token = _generate_token(user_id, username, email, device_id, client_ip, ACCESS_TOKEN_EXPIRY)
            
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
    """Set user session with access and refresh tokens bound to current device and IP
    
    SECURITY: Tokens are stored ONLY in session_state, not in database.
    When browser session ends, user must login again.
    Each token is bound to a specific device_id AND client_ip - cannot be used on different device/IP.
    """
    # Get or generate device_id and IP for this session
    device_id = _get_or_generate_device_id()
    client_ip = _get_client_ip()
    
    # Store IP in session state
    st.session_state.client_ip = client_ip
    
    # Generate tokens (both expire after 1 hour - auto logout enforced)
    # Both tokens are bound to this specific device AND IP address
    access_token = _generate_token(user_id, username, email, device_id, client_ip, ACCESS_TOKEN_EXPIRY)
    refresh_token = _generate_token(user_id, username, email, device_id, client_ip, REFRESH_TOKEN_EXPIRY)
    
    # Store in session state ONLY
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.email = email
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token

def logout_user():
    """Clear user session and tokens
    
    SECURITY: Completely wipes all session data to prevent data leakage between users.
    This is critical to ensure different users cannot see each other's data.
    """
    # CRITICAL SECURITY: Clear ALL session state to prevent data leakage
    # List of all known session state keys that must be cleared
    keys_to_clear = [
        # Authentication state
        'user_id', 'username', 'email', 
        'access_token', 'refresh_token',
        'device_id', 'client_ip',
        'auth_initialized',
        # App-specific data
        'stocks_loaded', 'portfolio_refreshed', 'chatbot_open',
        'chat_history',
        'stock_dfs', 'combined_df',
        'top_stocks_data', 'last_refresh_time',
        'stocks_data', 'session_id',
    ]
    
    # Clear all specified keys
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # CRITICAL: Force Streamlit to completely reset session
    # This ensures absolutely no residual data persists
    # Clear any remaining session state we might have missed
    # This is a nuclear option but necessary for security
    for key in list(st.session_state.keys()):
        if key not in ['_state', '_session_state']:  # Don't clear internal Streamlit state
            try:
                del st.session_state[key]
            except:
                pass

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
            # Validate device_id and IP match
            current_device_id = _get_or_generate_device_id()
            current_ip = _get_client_ip()
            token_device_id = payload.get('device_id')
            token_client_ip = payload.get('client_ip')
            
            if token_device_id != current_device_id or token_client_ip != current_ip:
                return False
            
            # Generate new access token with same device_id and client_ip
            access_token = _generate_token(
                payload['user_id'],
                payload['username'],
                payload['email'],
                payload['device_id'],
                payload['client_ip'],
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
        'device_id': st.session_state.get('device_id', 'Not generated yet'),
        'client_ip': st.session_state.get('client_ip', 'Not detected yet'),
        'has_access_token': 'access_token' in st.session_state and st.session_state.access_token is not None,
        'has_refresh_token': 'refresh_token' in st.session_state and st.session_state.refresh_token is not None,
        'is_logged_in': is_logged_in()
    }
    
    # If we have tokens, check device_id and IP binding
    if st.session_state.get('access_token'):
        payload = _decode_token(st.session_state.access_token)
        if payload:
            debug_info['token_device_id'] = payload.get('device_id')
            debug_info['token_client_ip'] = payload.get('client_ip')
            debug_info['device_match'] = payload.get('device_id') == st.session_state.get('device_id')
            debug_info['ip_match'] = payload.get('client_ip') == st.session_state.get('client_ip')
    
    return debug_info
