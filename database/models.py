"""Database Models and CRUD Operations"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import bcrypt
from bson import ObjectId
import database.connection as conn
from config import constants

# ===== USERS =====

def create_user(username: str, password: str, email: str) -> Optional[str]:
    """Create new user with hashed password"""
    db = conn.get_database()
    if db is None:
        return None
    
    # Check if user exists
    if db.users.find_one({"username": username}):
        return None
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Create user and initial portfolio
    user_id = db.users.insert_one({
        "username": username,
        "password_hash": password_hash,
        "email": email,
        "created_at": datetime.utcnow()
    }).inserted_id
    
    # Create initial portfolio
    create_portfolio(str(user_id))
    
    return str(user_id)

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate user and return user_id"""
    db = conn.get_database()
    if db is None:
        return None
    
    try:
        user = db.users.find_one({"username": username})
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return str(user["_id"])
        else:
            return None
    except Exception as e:
        return None

def get_user(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    db = conn.get_database()
    if db is None:
        return None
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except:
        return None

# ===== PORTFOLIOS =====

def create_portfolio(user_id: str) -> bool:
    """Create initial portfolio with 1M HKD"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.portfolios.insert_one({
        "user_id": user_id,
        "cash_balance": constants.INITIAL_CASH,
        "holdings": {},
        "holdings_details": {},  # Track purchase prices and dates
        "created_at": datetime.utcnow(),
        "last_refresh": datetime.utcnow()
    })
    return True

def get_portfolio(user_id: str) -> Optional[Dict]:
    """Get user portfolio"""
    db = conn.get_database()
    if db is None:
        return None
    
    return db.portfolios.find_one({"user_id": user_id})

def update_portfolio(user_id: str, updates: Dict) -> bool:
    """Update portfolio"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.portfolios.update_one({"user_id": user_id}, {"$set": updates})
    return True

def update_portfolio_refresh_time(user_id: str) -> bool:
    """Update last refresh time for portfolio"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.portfolios.update_one(
        {"user_id": user_id}, 
        {"$set": {"last_refresh": datetime.utcnow()}}
    )
    return True

def get_holdings_details(user_id: str) -> Dict:
    """Get detailed holdings with purchase prices"""
    portfolio = get_portfolio(user_id)
    if not portfolio:
        return {}
    
    return portfolio.get('holdings_details', {})

def update_holdings_details(user_id: str, ticker: str, purchase_price: float, purchase_date: datetime, quantity: float) -> bool:
    """Update holdings details with purchase information"""
    db = conn.get_database()
    if db is None:
        return False
    
    portfolio = get_portfolio(user_id)
    if not portfolio:
        return False
    
    holdings_details = portfolio.get('holdings_details', {})
    
    if ticker in holdings_details:
        # Update existing holding (average price calculation)
        existing = holdings_details[ticker]
        total_quantity = existing['quantity'] + quantity
        total_cost = (existing['quantity'] * existing['purchase_price']) + (quantity * purchase_price)
        avg_price = total_cost / total_quantity
        
        holdings_details[ticker] = {
            'quantity': total_quantity,
            'purchase_price': avg_price,
            'purchase_date': existing['purchase_date'],  # Keep original date
            'last_updated': datetime.utcnow()
        }
    else:
        # New holding
        holdings_details[ticker] = {
            'quantity': quantity,
            'purchase_price': purchase_price,
            'purchase_date': purchase_date,
            'last_updated': datetime.utcnow()
        }
    
    return update_portfolio(user_id, {'holdings_details': holdings_details})

def update_holding(user_id: str, ticker: str, quantity: float):
    """Update stock holding"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.portfolios.update_one(
        {"user_id": user_id},
        {"$set": {f"holdings.{ticker}": quantity}}
    )
    return True

# ===== TRANSACTIONS =====

def create_transaction(user_id: str, ticker: str, transaction_type: str, 
                      quantity: float, price: float) -> Optional[str]:
    """Create transaction record"""
    db = conn.get_database()
    if db is None:
        return None
    
    trans_id = db.transactions.insert_one({
        "user_id": user_id,
        "ticker": ticker,
        "type": transaction_type,  # 'buy' or 'sell'
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.utcnow()
    }).inserted_id
    
    return str(trans_id)

def get_transactions(user_id: str, limit: int = 100) -> List[Dict]:
    """Get user transactions"""
    db = conn.get_database()
    if db is None:
        return []
    
    cursor = db.transactions.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return list(cursor)

# ===== ALERTS =====

def create_alert(user_id: str, ticker: str, criteria: str, threshold: float, 
                active: bool = True) -> Optional[str]:
    """Create price alert"""
    db = conn.get_database()
    if db is None:
        return None
    
    alert_id = db.alerts.insert_one({
        "user_id": user_id,
        "ticker": ticker,
        "criteria": criteria,
        "threshold": threshold,
        "active": active,
        "created_at": datetime.utcnow(),
        "last_triggered": None
    }).inserted_id
    
    return str(alert_id)

def get_alerts(user_id: str, active_only: bool = True) -> List[Dict]:
    """Get user alerts"""
    db = conn.get_database()
    if db is None:
        return []
    
    query = {"user_id": user_id}
    if active_only:
        query["active"] = True
    
    return list(db.alerts.find(query).sort("created_at", -1))

def update_alert(alert_id: str, updates: Dict) -> bool:
    """Update alert"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.alerts.update_one({"_id": ObjectId(alert_id)}, {"$set": updates})
    return True

def delete_alert(alert_id: str) -> bool:
    """Delete alert"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.alerts.delete_one({"_id": ObjectId(alert_id)})
    return True

def get_users_with_active_alerts() -> List[Dict]:
    """Get all users who have active alerts"""
    db = conn.get_database()
    if db is None:
        return []
    
    try:
        # Get distinct user_ids from active alerts
        user_ids = db.alerts.distinct("user_id", {"active": True})
        users = []
        
        for user_id in user_ids:
            try:
                # Convert string user_id to ObjectId
                user_object_id = ObjectId(user_id)
                user = db.users.find_one({"_id": user_object_id})
                if user:
                    users.append({
                        "_id": user_id,
                        "email": user.get("email"),
                        "username": user.get("username")
                    })
            except Exception as e:
                continue
        
        return users
    except Exception as e:
        return []

def update_alert_last_triggered(alert_id: str):
    """Update last triggered timestamp"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"last_triggered": datetime.utcnow()}}
    )
    return True

# ===== CACHE =====

def get_cached_stock_data(ticker: str) -> Optional[Dict]:
    """Get cached stock data - check if data is from today"""
    db = conn.get_database()
    if db is None:
        return None
    
    cache_entry = db.stock_cache.find_one({"ticker": ticker})
    
    if cache_entry:
        cached_at = cache_entry.get("cached_at")
        if isinstance(cached_at, str):
            cached_at = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
        
        # Check if data is from today
        now = datetime.utcnow()
        if cached_at.date() == now.date():
            return cache_entry["data"]
    
    return None

def cache_stock_data(ticker: str, data: Dict):
    """Cache stock data with current date"""
    db = conn.get_database()
    if db is None:
        return
    
    db.stock_cache.update_one(
        {"ticker": ticker},
        {"$set": {
            "data": data,
            "cached_at": datetime.utcnow()
        }},
        upsert=True
    )

def get_all_cached_top_stocks():
    """Get all cached top 20 stocks"""
    db = conn.get_database()
    if db is None:
        return {}
    
    cache_entries = db.stock_cache.find({})
    result = {}
    now = datetime.utcnow()
    
    for entry in cache_entries:
        ticker = entry.get("ticker")
        cached_at = entry.get("cached_at")
        if isinstance(cached_at, str):
            cached_at = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
        
        # Only return data from today
        if cached_at.date() == now.date():
            result[ticker] = entry.get("data")
    
    return result

def get_cached_ai_response(query_hash: str) -> Optional[str]:
    """Get cached AI response"""
    db = conn.get_database()
    if db is None:
        return None
    
    cache_entry = db.ai_cache.find_one({"query_hash": query_hash})
    
    if cache_entry and datetime.utcnow() - cache_entry["cached_at"] < timedelta(hours=1):
        return cache_entry["response"]
    
    return None

def cache_ai_response(query_hash: str, response: str):
    """Cache AI response for 1 hour"""
    db = conn.get_database()
    if db is None:
        return
    
    db.ai_cache.update_one(
        {"query_hash": query_hash},
        {"$set": {
            "response": response,
            "cached_at": datetime.utcnow()
        }},
        upsert=True
    )

# ===== TOKEN MANAGEMENT =====

def save_tokens(user_id: str, access_token: str, refresh_token: str):
    """Save user tokens to database"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.user_tokens.update_one(
        {"user_id": user_id},
        {"$set": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    return True

def get_tokens(user_id: str) -> Optional[Dict]:
    """Get user tokens from database"""
    db = conn.get_database()
    if db is None:
        return None
    
    token_data = db.user_tokens.find_one({"user_id": user_id})
    if token_data:
        # Remove MongoDB _id field
        token_data.pop("_id", None)
    return token_data

def delete_tokens(user_id: str) -> bool:
    """Delete user tokens from database (logout)"""
    db = conn.get_database()
    if db is None:
        return False
    
    db.user_tokens.delete_one({"user_id": user_id})
    return True
