from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient

from app.config import settings

# MongoDB
mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
db = mongo_client.get_default_database()

knowledge_bases_collection = db["knowledge_bases"]
documents_collection = db["documents"]
chunks_collection = db["chunks"]
queries_collection = db["queries"]

# Qdrant
qdrant_client = QdrantClient(url=settings.qdrant_url)
