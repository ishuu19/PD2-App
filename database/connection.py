"""MongoDB Atlas Connection with Connection Pooling"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import config.api_keys as keys
from typing import Optional

_client: Optional[MongoClient] = None
_db = None

def get_client() -> Optional[MongoClient]:
    """Get MongoDB client with connection pooling"""
    global _client
    
    if _client is not None:
        try:
            _client.admin.command('ping')
            return _client
        except Exception:
            # Connection lost, recreate
            _client = None
    
    uri = keys.get_mongodb_uri()
    if not uri:
        print("❌ MongoDB URI not found in secrets or environment variables")
        return None
    
    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=10,
            minPoolSize=5
        )
        # Test connection
        _client.admin.command('ping')
        print("✅ MongoDB connection established successfully")
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return None

def get_database(db_name: str = "portfolio_management"):
    """Get database instance"""
    global _db
    client = get_client()
    if client:
        _db = client[db_name]
        print(f"✅ Connected to MongoDB database: {db_name}")
        return _db
    else:
        print(f"❌ Failed to connect to MongoDB database: {db_name}")
        return None

def close_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
