"""Main Portfolio Management Application"""
import streamlit as st
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
from config import constants

# Configure page
st.set_page_config(
    page_title="Login - Portfolio Management Platform",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'stocks_data' not in st.session_state:
    st.session_state.stocks_data = None

# Main app logic
def main():
    # Check if logged in
    if not auth.is_logged_in():
        # Hide sidebar for login page
        st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
        show_login_register()
    else:
        # Already configured at top, just show main app
        show_main_app()

def show_login_register():
    """Show login/register interface"""
    st.title("💰 Portfolio Management Platform")
    st.markdown("### Welcome! Please login or register to continue.")
    
    tabs = st.tabs(["Login", "Register"])
    
    with tabs[0]:
        # Login
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            if username and password:
                user_id = db.authenticate_user(username, password)
                if user_id:
                    user = db.get_user(user_id)
                    auth.login_user(user_id, username, user.get('email', ''))
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter username and password")
    
    with tabs[1]:
        # Register
        st.subheader("Register")
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        if st.button("Register", key="reg_btn"):
            if new_username and new_email and new_password:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_id = db.create_user(new_username, new_password, new_email)
                    if user_id:
                        st.success("Registration successful! Please login.")
                        st.rerun()
                    else:
                        st.error("Username already exists")
            else:
                st.warning("Please fill in all fields")

def show_main_app():
    """Show main application"""
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {auth.get_username()}!")
        
        # Load stock data
        if st.button("🔄 Refresh Stock Data"):
            with st.spinner("Loading stock data..."):
                st.session_state.stocks_data = stock_service.get_all_stocks()
                st.success("Data loaded!")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### Navigation")
        st.markdown("- [Portfolio Dashboard](#portfolio-dashboard)")
        st.markdown("- [AI Predictions](#ai-predictions)")
        st.markdown("- [Email Alerts](#email-alerts)")
        st.markdown("- [Market Intelligence](#market-intelligence)")
        
        st.markdown("---")
        
        # Portfolio summary
        st.markdown("### Portfolio Summary")
        portfolio = db.get_portfolio(auth.get_user_id())
        if portfolio:
            st.metric("Cash Balance", f"${portfolio.get('cash_balance', 0):,.0f} USD")
            
            # Calculate portfolio value if stocks data is loaded
            if st.session_state.stocks_data:
                from services import portfolio_service
                portfolio_value = portfolio_service.calculate_portfolio_value(
                    auth.get_user_id(), 
                    st.session_state.stocks_data
                )
                if portfolio_value:
                    st.metric("Total Value", f"${portfolio_value.get('total_value', 0):,.0f} USD")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout_user()
            st.rerun()
    
    # Main content
    st.title("Portfolio Management Platform")
    
    # Load stocks if not loaded
    if st.session_state.stocks_data is None:
        with st.spinner("Loading stock data for the first time..."):
            st.session_state.stocks_data = stock_service.get_all_stocks()
    
    # Display stock data info
    num_stocks_loaded = sum(1 for v in st.session_state.stocks_data.values() if v is not None) if st.session_state.stocks_data else 0
    st.info(f"📊 {num_stocks_loaded} stocks loaded. Use the sidebar to refresh data.")
    
    # Main content will be handled by Streamlit pages
    st.markdown("""
    ## Welcome to Your Portfolio Management Dashboard
    
    Use the navigation in the sidebar to explore different features:
    
    1. **Portfolio Dashboard** - View your holdings, buy/sell stocks, and get AI recommendations
    2. **AI Predictions** - Get AI-powered price predictions and trading signals
    3. **Email Alerts** - Set up intelligent email alerts for your stocks
    4. **Market Intelligence** - Advanced market analysis and insights
    
    Use the refresh button in the sidebar to update stock prices.
    """)

if __name__ == "__main__":
    main()
