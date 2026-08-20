from pymongo import AsyncMongoClient

from backend.app.config import settings


client = AsyncMongoClient(settings.mongodb_uri)

database = client[settings.mongodb_database]