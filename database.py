import os
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_DETAILS = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = AsyncIOMotorClient(MONGO_DETAILS, serverSelectionTimeoutMS=2000)
    database = client.flight_fare_db
    chat_history_collection = database.get_collection("chat_history")
    
    # Check connection
    client.admin.command('ping')
    USE_MONGODB = True
    logger.info("Successfully connected to MongoDB.")
except Exception as e:
    logger.warning(f"Could not connect to MongoDB. Using in-memory fallback. Error: {e}")
    USE_MONGODB = False
    
# In-memory fallback
fallback_chat_history = []

async def save_chat_message(session_id: str, message: str, sender: str):
    """Save a single chat message to MongoDB or Fallback."""
    doc = {
        "session_id": session_id,
        "message": message,
        "sender": sender
    }
    if USE_MONGODB:
        try:
            await chat_history_collection.insert_one(doc)
        except Exception as e:
            logger.error(f"Failed to save to MongoDB: {e}")
            fallback_chat_history.append(doc)
    else:
        fallback_chat_history.append(doc)

async def get_chat_history(session_id: str):
    """Retrieve chat history for a given session."""
    messages = []
    if USE_MONGODB:
        try:
            cursor = chat_history_collection.find({"session_id": session_id}).sort("_id", 1)
            async for document in cursor:
                messages.append({
                    "message": document["message"],
                    "sender": document["sender"]
                })
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve from MongoDB: {e}")
    
    # Fallback retrieval
    for doc in fallback_chat_history:
        if doc["session_id"] == session_id:
            messages.append({
                "message": doc["message"],
                "sender": doc["sender"]
            })
    return messages
