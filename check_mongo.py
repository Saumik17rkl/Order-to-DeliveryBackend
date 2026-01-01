"""
MongoDB Connection and Setup Check Script
"""
from app.mongo import get_mongo_db
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import sys

def check_mongodb_connection():
    """Check MongoDB connection and basic operations"""
    try:
        # Test connection
        print("🔍 Testing MongoDB connection...")
        db = get_mongo_db()
        
        # Test if connection is working
        db.command('ping')
        print("✅ Successfully connected to MongoDB")
        
        # Check collections
        collections = db.list_collection_names()
        print("\n📂 Available collections:", collections)
        
        # Check inventory collection
        print("\n📦 Checking inventory collection...")
        inventory_count = db.inventory.count_documents({})
        print(f"   Found {inventory_count} items in inventory")
        if inventory_count > 0:
            print("   Sample item:", db.inventory.find_one({}, {'_id': 0, 'sku': 1, 'name': 1, 'stock': 1}))
        
        # Check orders collection
        print("\n📝 Checking orders collection...")
        orders_count = db.orders.count_documents({})
        print(f"   Found {orders_count} orders")
        if orders_count > 0:
            print("   Most recent order:", db.orders.find_one(
                {}, 
                {'_id': 0, 'order_id': 1, 'customer_name': 1, 'status': 1, 'created_at': 1},
                sort=[('order_id', -1)]
            ))
        
        # Check or initialize order counter
        print("\n🔢 Checking order counter...")
        counter = db.counters.find_one({"_id": "order_id"})
        if counter:
            print(f"   Current order ID counter: {counter['seq']}")
        else:
            print("   Initializing order ID counter...")
            db.counters.insert_one({"_id": "order_id", "seq": 1})
            print("   ✅ Order ID counter initialized to 1")
        
        # Test write operation
        print("\n✏️  Testing write operation...")
        test_collection = db.get_collection("test_connection")
        test_collection.insert_one({"test": "connection_successful", "timestamp": "now"})
        test_collection.drop()  # Clean up
        print("   ✅ Write test successful")
        
        print("\n✨ MongoDB connection and setup check completed successfully!")
        
    except ConnectionFailure as e:
        print("❌ Failed to connect to MongoDB")
        print("Error:", str(e))
        print("\nPlease check:")
        print("1. Is MongoDB running?")
        print("2. Is the connection string in .env correct?")
        print("3. Is the network accessible?")
        sys.exit(1)
    except OperationFailure as e:
        print("❌ MongoDB operation failed")
        print("Error:", str(e))
        print("\nPlease check:")
        print("1. Do you have the correct permissions?")
        print("2. Is the database name correct?")
        sys.exit(1)
    except Exception as e:
        print("❌ An unexpected error occurred")
        print("Error:", str(e))
        print("\nPlease check the error message above for details")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting MongoDB connection check...\n")
    check_mongodb_connection()
