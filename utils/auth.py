"""Authentication Helper Functions with JWT Tokens and Persistent Storage"""
import streamlit as st
import jwt
from datetime import datetime, timedelta
import os
import database.models as db
import json
import pickle

# Secret key for JWT signing
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_secret_key_change_in_production')

# Token expiration times
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # Short-lived access token
REFRESH_TOKEN_EXPIRY = timedelta(days=7)  # Long-lived refresh token

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

def _get_persistent_auth():
    """Get authentication data from persistent storage (cookies/localStorage)"""
    try:
        # Try to get from Streamlit's experimental cookie manager
        if hasattr(st, 'experimental_user'):
            # This is a placeholder - Streamlit doesn't have built-in cookie access
            # We'll use a different approach
            pass
    except:
        pass
    return None

def _save_persistent_auth(user_data):
    """Save authentication data to persistent storage"""
    try:
        # This is a placeholder - we'll use database as primary persistent storage
        pass
    except:
        pass

def _get_persistent_user_id():
    """Get persistent user ID from session state, file, or URL parameters"""
    # First check if we already have user data in session state
    if st.session_state.get('user_id'):
        return st.session_state.user_id
    
    # Check if we have a stored user_id in session state
    if 'persistent_user_id' in st.session_state and st.session_state.persistent_user_id:
        return st.session_state.persistent_user_id
    
    # Check file-based storage (survives page refresh)
    user_file = '.streamlit/.user_id'
    if os.path.exists(user_file):
        try:
            with open(user_file, 'r') as f:
                user_id = f.read().strip()
                if user_id:
                    st.session_state.persistent_user_id = user_id
                    return user_id
        except:
            pass
    
    # Check URL parameters as fallback (for redirect after login)
    if 'user_id' in st.query_params and st.query_params.user_id:
        user_id = st.query_params.user_id
        st.session_state.persistent_user_id = user_id
        # Save to file for persistence
        try:
            os.makedirs('.streamlit', exist_ok=True)
            with open(user_file, 'w') as f:
                f.write(user_id)
        except:
            pass
        return user_id
    
    return None

def _set_persistent_user_id(user_id):
    """Set persistent user ID in session state and file"""
    st.session_state.persistent_user_id = user_id
    
    # Save to file for persistence across refreshes
    try:
        os.makedirs('.streamlit', exist_ok=True)
        with open('.streamlit/.user_id', 'w') as f:
            f.write(user_id)
    except:
        pass

def is_logged_in():
    """Check if user is logged in with persistent authentication across page refreshes"""
    # Initialize session state if not exists
    if 'auth_initialized' not in st.session_state:
        st.session_state.auth_initialized = True
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        
        # On first initialization, try to restore from URL or database
        # Check URL parameters first
        if 'user_id' in st.query_params and st.query_params.user_id:
            user_id = st.query_params.user_id
            st.session_state.persistent_user_id = user_id
            
            # Try to restore session from database
            token_data = db.get_tokens(user_id)
            if token_data:
                stored_access_token = token_data.get('access_token')
                stored_refresh_token = token_data.get('refresh_token')
                
                # Try stored access token first
                if stored_access_token:
                    payload = _decode_token(stored_access_token)
                    if payload:
                        # Restore session immediately
                        st.session_state.user_id = payload['user_id']
                        st.session_state.username = payload['username']
                        st.session_state.email = payload['email']
                        st.session_state.access_token = stored_access_token
                        st.session_state.refresh_token = stored_refresh_token
                        return True
                
                # Try stored refresh token
                if stored_refresh_token:
                    payload = _decode_token(stored_refresh_token)
                    if payload:
                        # Generate new access token and restore session
                        user_id_from_token = payload['user_id']
                        username = payload['username']
                        email = payload['email']
                        
                        new_access_token = _generate_token(user_id_from_token, username, email, ACCESS_TOKEN_EXPIRY)
                        
                        st.session_state.user_id = user_id_from_token
                        st.session_state.username = username
                        st.session_state.email = email
                        st.session_state.access_token = new_access_token
                        st.session_state.refresh_token = stored_refresh_token
                        
                        db.save_tokens(user_id_from_token, new_access_token, stored_refresh_token)
                        return True
    
    # First check if we already have valid tokens in session state
    access_token = st.session_state.get('access_token')
    if access_token:
        payload = _decode_token(access_token)
        if payload:
            # Valid access token in session state
            if 'user_id' not in st.session_state or st.session_state.user_id is None:
                # Restore user info from token
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
            
            # Save to database
            db.save_tokens(user_id, new_access_token, refresh_token)
            _set_persistent_user_id(user_id)
            
            return True
    
    # Get persistent user ID from URL or session
    persistent_user_id = _get_persistent_user_id()
    
    # Try to restore using persistent user ID if we have one
    if persistent_user_id:
        token_data = db.get_tokens(persistent_user_id)
        
        if token_data:
            stored_access_token = token_data.get('access_token')
            stored_refresh_token = token_data.get('refresh_token')
            
            # Try stored access token first
            if stored_access_token:
                payload = _decode_token(stored_access_token)
                if payload:
                    # Valid access token from database, restore session
                    st.session_state.user_id = payload['user_id']
                    st.session_state.username = payload['username']
                    st.session_state.email = payload['email']
                    st.session_state.access_token = stored_access_token
                    st.session_state.refresh_token = stored_refresh_token
                    return True
            
            # Try stored refresh token
            if stored_refresh_token:
                payload = _decode_token(stored_refresh_token)
                if payload:
                    # Valid refresh token from database, generate new access token
                    user_id = payload['user_id']
                    username = payload['username']
                    email = payload['email']
                    
                    new_access_token = _generate_token(user_id, username, email, ACCESS_TOKEN_EXPIRY)
                    
                    # Update session state and database
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.email = email
                    st.session_state.access_token = new_access_token
                    st.session_state.refresh_token = stored_refresh_token
                    db.save_tokens(user_id, new_access_token, stored_refresh_token)
                    _set_persistent_user_id(user_id)
                    st.query_params['user_id'] = user_id
                    
                    return True
    
    # No valid authentication found
    return False

def _clear_session_state():
    """Clear authentication from session state"""
    keys_to_clear = ['user_id', 'username', 'email', 'access_token', 'refresh_token']
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

def login_user(user_id: str, username: str, email: str):
    """Set user session with access and refresh tokens"""
    # Generate tokens (1 hour access token, 7 days refresh token)
    access_token = _generate_token(user_id, username, email, ACCESS_TOKEN_EXPIRY)
    refresh_token = _generate_token(user_id, username, email, REFRESH_TOKEN_EXPIRY)
    
    # Set persistent user ID FIRST - needed for is_logged_in to work
    _set_persistent_user_id(user_id)
    
    # Store in session state
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.email = email
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    
    # Save to database for persistence across refreshes
    db.save_tokens(user_id, access_token, refresh_token)

def logout_user():
    """Clear user session and tokens"""
    user_id = st.session_state.get('user_id')
    
    # Delete from database
    if user_id:
        db.delete_tokens(user_id)
    
    # Clear persistent user ID file
    user_file = '.streamlit/.user_id'
    if os.path.exists(user_file):
        try:
            os.remove(user_file)
        except:
            pass
    
    # Clear persistent user ID from session
    if 'persistent_user_id' in st.session_state:
        del st.session_state['persistent_user_id']
    
    # Clear URL parameters
    if 'user_id' in st.query_params:
        del st.query_params['user_id']
    
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
        'persistent_user_id': st.session_state.get('persistent_user_id'),
        'url_user_id': st.query_params.get('user_id'),
        'is_logged_in': is_logged_in()
    }
    
    # Check database tokens if we have a user_id
    if st.session_state.get('user_id'):
        token_data = db.get_tokens(st.session_state.user_id)
        debug_info['database_has_tokens'] = token_data is not None
        if token_data:
            debug_info['database_access_token_valid'] = _decode_token(token_data.get('access_token')) is not None
            debug_info['database_refresh_token_valid'] = _decode_token(token_data.get('refresh_token')) is not None
    
    return debug_info
