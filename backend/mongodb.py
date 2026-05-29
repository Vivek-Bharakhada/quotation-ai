import os
import time
from datetime import datetime
import pymongo

MONGO_URI = str(os.getenv("MONGO_URI", "")).strip()

_client = None

def get_db():
    global _client
    if not MONGO_URI:
        return None
    if _client is None:
        try:
            # Short timeout to avoid application hang if offline/invalid URI
            _client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Trigger connection check
            _client.admin.command('ping')
        except Exception as e:
            print(f"Warning: Failed to connect to MongoDB: {e}")
            _client = None
            return None
    return _client["quotation_ai"]

def is_enabled() -> bool:
    if not MONGO_URI:
        return False
    try:
        db = get_db()
        return db is not None
    except Exception:
        return False

def save_quote(quote_id: str, data: dict):
    db = get_db()
    if db is None:
        return
    doc = dict(data)
    doc["_id"] = quote_id
    doc["updated_at"] = datetime.utcnow()
    db["quotes"].replace_one({"_id": quote_id}, doc, upsert=True)

def list_quotes():
    db = get_db()
    if db is None:
        return []
    cursor = db["quotes"].find({}, {"client_name": 1, "grand_total": 1, "updated_at": 1})
    cursor = cursor.sort("updated_at", pymongo.DESCENDING)
    
    details = []
    for doc in cursor:
        updated_at = doc.get("updated_at")
        ts = updated_at.timestamp() if isinstance(updated_at, datetime) else time.time()
        details.append({
            "id": doc["_id"],
            "client": doc.get("client_name", "N/A"),
            "total": doc.get("grand_total", 0),
            "date": ts
        })
    return details

def load_quote(quote_id: str):
    db = get_db()
    if db is None:
        return None
    doc = db["quotes"].find_one({"_id": quote_id})
    if doc:
        doc.pop("_id", None)
        doc.pop("updated_at", None)
    return doc

def delete_quote(quote_id: str) -> bool:
    db = get_db()
    if db is None:
        return False
    res = db["quotes"].delete_one({"_id": quote_id})
    return res.deleted_count > 0

def load_search_index():
    db = get_db()
    if db is None:
        return None
    try:
        doc = db["search_index"].find_one({"_id": "global"})
        if doc:
            doc.pop("_id", None)
        return doc
    except Exception as e:
        print(f"Warning: Failed to load search index from MongoDB: {e}")
        return None

def save_search_index(data: dict):
    db = get_db()
    if db is None:
        return
    try:
        doc = dict(data)
        doc["_id"] = "global"
        db["search_index"].replace_one({"_id": "global"}, doc, upsert=True)
        print("Successfully saved search index to MongoDB!")
    except Exception as e:
        print(f"Warning: Failed to save search index to MongoDB: {e}")
