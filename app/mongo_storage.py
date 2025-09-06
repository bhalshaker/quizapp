import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING
from config import mongo_config

_cfg = mongo_config()
_client: Optional[MongoClient] = None
_db = None

def _get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(_cfg["uri"])
        _db = _client[_cfg["db_name"]]
        _ensure_indexes()
    return _db

def _ensure_indexes():
    db = _db
    if db is None:
        return
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.results.create_index([("email", ASCENDING), ("timestamp", ASCENDING)])
    db.results.create_index([("topic_id", ASCENDING)])
    db.topics.create_index([("topic_id", ASCENDING)], unique=True)
    db.topics.create_index([("topic_name", ASCENDING)], unique=True)

# -------- Users --------

def get_users() -> List[Dict[str, Any]]:
    db = _get_db()
    return list(db.users.find({}, {"_id": 0}).sort("email", ASCENDING))

def delete_user(email: str) -> bool:
    db = _get_db()
    res = db.users.delete_one({"email": email})
    # Optionally cascade delete results:
    # db.results.delete_many({"email": email})
    return res.deleted_count == 1

def create_user(email: str, name: str, hashed_pw: str, role: str) -> bool:
    db = _get_db()
    if db.users.find_one({"email": email}):
        return False
    user_doc = {
        "email": email,
        "name": name,
        "password": hashed_pw,
        "role": role
    }
    user_doc.pop("username", None)  # Defensive cleanup
    db.users.insert_one(user_doc)
    return True

def update_user(email: str, updates: Dict[str, Any]) -> bool:
    db = _get_db()
    updates.pop("username", None)  # Defensive cleanup
    result = db.users.update_one({"email": email}, {"$set": updates})
    return result.modified_count > 0

# -------- Results --------

def save_result_mongo(email: str, question_id: Any, user_answers: List[str], correct_answers: List[str], score: int, topic_id: Optional[str] = None) -> None:
    db = _get_db()
    db.results.insert_one({
        "email": email,
        "question_id": question_id,
        "user_answers": user_answers,
        "correct_answers": correct_answers,
        "score": score,
        "timestamp": datetime.utcnow().isoformat(),
        "topic_id": topic_id,
    })

def get_user_results(email: str) -> List[Dict[str, Any]]:
    db = _get_db()
    return list(db.results.find({"email": email}, {"_id": 0}).sort("timestamp", ASCENDING))

# -------- Topics --------

def save_topic(topic_name: str, questions: List[Dict[str, Any]]) -> str:
    db = _get_db()
    topic_id = str(uuid.uuid4())
    db.topics.insert_one({
        "topic_id": topic_id,
        "topic_name": topic_name,
        "questions": questions,
        "created_at": datetime.utcnow().isoformat()
    })
    return topic_id

def get_all_topics() -> List[Dict[str, str]]:
    db = _get_db()
    cursor = db.topics.find({}, {"_id": 0, "topic_id": 1, "topic_name": 1}).sort("topic_name", ASCENDING)
    return list(cursor)

def get_topic_questions(topic_id: str) -> List[Dict[str, Any]]:
    db = _get_db()
    doc = db.topics.find_one({"topic_id": topic_id}, {"_id": 0, "questions": 1})
    return doc.get("questions", []) if doc else []

def delete_topic(topic_id: str) -> bool:
    db = _get_db()
    res = db.topics.delete_one({"topic_id": topic_id})
    return res.deleted_count == 1

# -------- Validation --------

def validate_questions(questions: Any) -> List[str]:
    issues = []
    if not isinstance(questions, list):
        return ["Root must be a list of questions."]
    for i, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            issues.append(f"Q{i}: must be an object.")
            continue
        for field in ["id", "text", "options", "correct", "type", "points"]:
            if field not in q:
                issues.append(f"Q{i}: missing '{field}'.")
        if "options" in q and not isinstance(q["options"], dict):
            issues.append(f"Q{i}: 'options' must be an object.")
        if "correct" in q and not isinstance(q["correct"], list):
            issues.append(f"Q{i}: 'correct' must be a list of labels.")
        if "image" in q and q["image"] and not isinstance(q["image"], str):
            issues.append(f"Q{i}: 'image' must be a string URL if present.")
        if "category" in q and q["category"] and not isinstance(q["category"], str):
            issues.append(f"Q{i}: 'category' must be a string if present.")
        if "difficulty" in q and q["difficulty"] and not isinstance(q["difficulty"], str):
            issues.append(f"Q{i}: 'difficulty' must be a string if present.")
    return issues
