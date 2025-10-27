"""Main Portfolio Management Application"""
import streamlit as st
import utils.auth as auth
import database.models as db
import services.stock_data as stock_service
import components.chatbot as chatbot
from config import constants

# Configure page (default to wide layout for dashboard)
st.set_page_config(
    page_title="Portfolio Management",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'email' not in st.session_state:
    st.session_state.email = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'stocks_data' not in st.session_state:
    st.session_state.stocks_data = {}
if 'persistent_user_id' not in st.session_state:
    st.session_state.persistent_user_id = None

# Debug authentication (only show in development)
if st.sidebar.checkbox("🔧 Debug Authentication", help="Show authentication debug information"):
    debug_info = auth.debug_auth_status()
    st.sidebar.write("**Auth Debug Info:**")
    for key, value in debug_info.items():
        st.sidebar.write(f"- {key}: {value}")
    
    if st.sidebar.button("🔄 Refresh Auth"):
        st.rerun()

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
        # Show dashboard for logged in users
        show_main_app()
        # Render chatbot on all pages when logged in
        chatbot.render_chatbot()

def show_login_register():
    """Show login/register interface"""
    # Center the content using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("💰 Portfolio Management Platform")
        st.markdown("### Welcome! Please login or register to continue.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tabs = st.tabs(["Login", "Register"])
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with tabs[0]:
            # Login
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_btn", use_container_width=True):
                if username and password:
                    user_id = db.authenticate_user(username, password)
                    if user_id:
                        user = db.get_user(user_id)
                        auth.login_user(user_id, username, user.get('email', ''))
                        st.success("Login successful! Redirecting to Dashboard...")
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
            
            if st.button("Register", key="reg_btn", use_container_width=True):
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
    """Show main application - Dashboard"""
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {auth.get_username()}!")
        
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
    
    # Main content - Dashboard
    st.title("📊 Dashboard")
    
    # Welcome message
    st.markdown(f"### Welcome back, {auth.get_username()}! 👋")
    
    # Stock Search Section
    st.markdown("---")
    st.header("🔍 Search Stock")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input("Enter Stock Ticker", key="main_ticker_search", placeholder="e.g., AAPL, MSFT, GOOGL")
    with col2:
        search_button = st.button("Search", use_container_width=True, type="primary")
    
    # Handle search
    if search_button and ticker_input:
        ticker = ticker_input.upper()
        
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data = stock_service.get_stock_data(ticker, use_cache=False)
        
        if stock_data:
            st.success(f"✓ Data loaded for {stock_data['name']} ({ticker})")
            
            # Display stock metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${stock_data['current_price']:.2f}")
            with col2:
                st.metric("Change %", f"{stock_data['change_percent']:.2f}%", 
                         delta=f"{stock_data['change_percent']:.2f}%")
            with col3:
                st.metric("Volume", f"{stock_data['volume']:,}")
            with col4:
                st.metric("Volatility", f"{stock_data['volatility']:.2f}%")
            
            # Expanded metrics
            with st.expander("View All Metrics"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("52W High", f"${stock_data['high_52w']:.2f}")
                    st.metric("1M Return", f"{stock_data['returns_1m']:.2f}%")
                    st.metric("3M Return", f"{stock_data['returns_3m']:.2f}%")
                with col2:
                    st.metric("52W Low", f"${stock_data['low_52w']:.2f}")
                    st.metric("6M Return", f"{stock_data['returns_6m']:.2f}%")
                    st.metric("1Y Return", f"{stock_data['returns_1y']:.2f}%")
                with col3:
                    st.metric("Beta", f"{stock_data['beta']:.2f}")
                    st.metric("P/E Ratio", f"{stock_data['pe_ratio']:.2f}")
                    st.metric("Dividend Yield", f"{stock_data['dividend_yield']:.2f}%")
            
            # Add or update stock data
            st.session_state.stocks_data[ticker] = stock_data
            
            st.success(f"✓ Stock {ticker} has been added to your analysis. Go to Portfolio Dashboard to buy/sell stocks.")
        else:
            st.error(f"Could not fetch data for {ticker}. Please check the ticker symbol and try again.")
    
    st.markdown("---")
    
    # Display currently loaded stocks
    if not st.session_state.stocks_data:
        st.info("👈 Search for a stock ticker above to get started.")
    else:
        num_stocks_loaded = sum(1 for v in st.session_state.stocks_data.values() if v is not None)
        if num_stocks_loaded > 0:
            st.success(f"📊 {num_stocks_loaded} stock(s) loaded. Visit Portfolio Dashboard to view details.")
            # Show list of loaded stocks
            with st.expander("View Loaded Stocks"):
                for ticker, data in st.session_state.stocks_data.items():
                    if data:
                        st.text(f"• {ticker} - {data.get('name', 'N/A')}")
    
    # Main content will be handled by Streamlit pages
    st.markdown("""
    ## Welcome to Your Portfolio Management Dashboard
    
    Use the navigation in the sidebar to explore different features:
    
    1. **Portfolio Dashboard** - View your holdings, buy/sell stocks, and get AI recommendations
    2. **AI Predictions** - Get AI-powered price predictions and trading signals
    3. **Email Alerts** - Set up intelligent email alerts for your stocks
    4. **Market Intelligence** - Advanced market analysis and insights
    """)

if __name__ == "__main__":
    main()
