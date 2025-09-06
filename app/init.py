from pymongo import MongoClient
import streamlit_authenticator_mongo as stauth
from config import mongo_config

cfg = mongo_config()
client = MongoClient(cfg["uri"])

# 🔍 Drop index BEFORE dropping the database
try:
    client[cfg["db_name"]]["users"].drop_index("username_1")
    print("✅ Dropped index 'username_1'")
except Exception as e:
    print("⚠️ Index 'username_1' not found or already dropped:", e)

# 🚨 Drop and recreate the database
client.drop_database(cfg["db_name"])
db = client[cfg["db_name"]]
users = db["users"]

# ✅ Create unique index on email
users.create_index("email", unique=True)
print("✅ Created unique index on 'email'")

# 🧹 Clean up any leftover 'username' fields
users.update_many({}, {"$unset": {"username": ""}})
print("✅ Removed 'username' field from all users")

# 🔐 Seed admin user
hashed_pw = stauth.Hasher(["admin123"]).generate()[0]

users.insert_one({
    "email": "admin@example.com",
    "password": hashed_pw,
    "name": "Quiz App Admin",
    "role": "admin"
})
for idx in users.list_indexes():
    print(idx)
print("✅ Database reset complete. Admin user created.")
