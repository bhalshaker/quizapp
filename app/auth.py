import streamlit_authenticator_mongo as stauth
import yaml
from yaml.loader import SafeLoader
from pymongo import MongoClient
from config import mongo_config

def get_authenticator():
    cfg = mongo_config()
    client = MongoClient(cfg["uri"])
    db = client[cfg["db_name"]]
    users_collection = db["users"]

    # Load cookie config
    with open("auth_config.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Build credentials dict using email as key
    credentials = {"usernames": {}}
    for user in users_collection.find():
        if not all(k in user for k in ("email", "password", "name")):
            print(f"⚠️ Skipping invalid user document: {user}")
            continue

        credentials["usernames"][user["email"]] = {
            "email": user["email"],
            "name": user["name"],
            "password": user["password"],
            "role": user.get("role", "user")
        }

    authenticator = stauth.Authenticate(
        credentials,
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        config.get("preauthorized", {})
    )

    # Attach raw Mongo collection for later lookups
    authenticator.collection = users_collection
    return authenticator
