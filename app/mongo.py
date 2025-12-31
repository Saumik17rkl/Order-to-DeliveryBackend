from functools import lru_cache

from pymongo import MongoClient
from pymongo.server_api import ServerApi

from app.settings import settings


@lru_cache
def get_mongo_client() -> MongoClient:
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not set")
    return MongoClient(settings.mongodb_uri, server_api=ServerApi("1"))


def get_mongo_db():
    client = get_mongo_client()
    return client[settings.mongodb_db]
