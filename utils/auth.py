"""Authentication Helper Functions"""
import streamlit as st

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in st.session_state and st.session_state.user_id is not None

def login_user(user_id: str, username: str, email: str):
    """Set user session"""
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.email = email

def logout_user():
    """Clear user session"""
    for key in ['user_id', 'username', 'email']:
        if key in st.session_state:
            del st.session_state[key]

def get_user_id():
    """Get current user ID"""
    return st.session_state.get('user_id')

def get_username():
    """Get current username"""
    return st.session_state.get('username', 'Guest')
