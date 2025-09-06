import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    return {
        "file_path": os.getenv("DEFAULT_QUESTION_FILE", "questions.json"),
        "duration_minutes": int(os.getenv("DEFAULT_DURATION_MINUTES", 5)),
        "num_questions": int(os.getenv("DEFAULT_NUM_QUESTIONS", 5)),
    }

def mongo_config():
    return {
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "db_name": os.getenv("MONGO_DB", "quizapp"),
    }
