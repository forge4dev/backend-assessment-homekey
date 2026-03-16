import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "homekey_assessment")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_REDIS_URL = REDIS_URL
    VALUATION_TIMEOUT_MS = int(os.environ.get("VALUATION_TIMEOUT_MS", 5000))
