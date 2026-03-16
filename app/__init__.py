from flask import Flask
from pymongo import MongoClient
import redis

from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # MongoDB
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client[app.config["MONGO_DB_NAME"]]

    # Redis
    app.redis = redis.Redis.from_url(app.config["REDIS_URL"], decode_responses=True)

    # Blueprints
    from app.routes.property_routes import property_bp
    app.register_blueprint(property_bp, url_prefix="/api/v1/properties")

    return app
