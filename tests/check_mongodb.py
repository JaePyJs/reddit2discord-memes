"""
Quick MongoDB Connection Tester

This script tests your MongoDB connection and verifies that your .env settings are correctly configured.
It also provides some basic commands for exploring your MongoDB database.

Usage: python check_mongodb.py
"""

import os
import sys
import pymongo
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

def print_header(title):
    """Print a styled header."""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "="))
    print("=" * 70 + "\n")

def print_section(title):
    """Print a section title."""
    print(f"\n--- {title} ---")

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️ {message}")

def main():
    # Load environment variables
    print_header("MongoDB Connection Tester")
    
    print_section("Loading Environment Variables")
    load_dotenv()
    
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "discord_meme_bot")
    use_mongo_ai = os.getenv("USE_MONGO_FOR_AI", "True").lower() in ('true', '1', 't')
    
    print_info(f"MongoDB URI: {mongo_uri}")
    print_info(f"Database Name: {db_name}")
    print_info(f"MongoDB for AI enabled: {use_mongo_ai}")
    
    if not use_mongo_ai:
        print_error("MongoDB for AI is disabled in your .env file.")
        print_info("To enable it, set USE_MONGO_FOR_AI=True in your .env file.")
    
    print_section("Testing MongoDB Connection")
    try:
        # Set a shorter timeout for quicker feedback
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Ping the server to verify connection
        client.admin.command('ping')
        
        print_success("Successfully connected to MongoDB server!")
        
        # Check if database exists
        db_list = client.list_database_names()
        if db_name in db_list:
            print_success(f"Found database: {db_name}")
        else:
            print_error(f"Database '{db_name}' not found.")
            print_info("You need to run init_mongodb.py to create the database.")
            return
        
        # Connect to the database
        db = client[db_name]
        
        # Check for required collections
        expected_collections = ["ai_channels", "ai_conversations", "ai_messages", "ai_user_preferences"]
        
        print_section("Checking Required Collections")
        collections = db.list_collection_names()
        
        for collection in expected_collections:
            if collection in collections:
                doc_count = db[collection].count_documents({})
                print_success(f"Found collection: {collection} ({doc_count} documents)")
            else:
                print_error(f"Collection '{collection}' not found.")
                print_info("Run init_mongodb.py to create all required collections.")
        
        # Provide information for exploring data
        print_section("MongoDB Data Explorer")
        print_info("Use MongoDB Compass to explore your data with these steps:")
        print("1. Open MongoDB Compass")
        print("2. Connect to your MongoDB server")
        print(f"3. Select the '{db_name}' database")
        print("4. Click on a collection to view its documents")
        print("5. Use the filter bar to query documents")
        
        # Provide commands for common operations
        print_section("Common MongoDB Shell Commands")
        print("To view all documents in a collection:")
        print(f"   db.ai_channels.find()")
        print("To find a specific document:")
        print(f"   db.ai_channels.find({{'guild_id': '123456789'}})")
        print("To count documents in a collection:")
        print(f"   db.ai_messages.countDocuments()")
        
    except ServerSelectionTimeoutError as e:
        print_error("Could not connect to MongoDB server.")
        print_info("Is your MongoDB server running?")
        print_info("Check that your MONGO_URI is correct in the .env file.")
        print(f"Error details: {e}")
    except ConnectionFailure as e:
        print_error("Failed to connect to MongoDB server.")
        print(f"Error details: {e}")
    except OperationFailure as e:
        print_error("Authentication failed.")
        print_info("Check your MongoDB username and password.")
        print(f"Error details: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
    finally:
        # Close the MongoDB connection if it was opened
        if 'client' in locals():
            client.close()
            print_info("MongoDB connection closed.")

if __name__ == "__main__":
    main()
