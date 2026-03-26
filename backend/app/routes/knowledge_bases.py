from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database import knowledge_bases_collection, documents_collection, chunks_collection, queries_collection
from app.models.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse
from app.services.retriever import delete_collection

router = APIRouter(tags=["Knowledge Bases"])


@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(kb: KnowledgeBaseCreate):
    doc = {
        "name": kb.name,
        "description": kb.description,
        "document_count": 0,
        "created_at": datetime.now(timezone.utc),
    }
    result = await knowledge_bases_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return KnowledgeBaseResponse.from_mongo(doc)


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases():
    cursor = knowledge_bases_collection.find().sort("created_at", -1)
    return [KnowledgeBaseResponse.from_mongo(doc) async for doc in cursor]


@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str):
    doc = await knowledge_bases_collection.find_one({"_id": ObjectId(kb_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBaseResponse.from_mongo(doc)


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    kb = await knowledge_bases_collection.find_one({"_id": ObjectId(kb_id)})
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Delete all related data
    await chunks_collection.delete_many({"knowledge_base_id": ObjectId(kb_id)})
    await documents_collection.delete_many({"knowledge_base_id": ObjectId(kb_id)})
    await queries_collection.delete_many({"knowledge_base_id": ObjectId(kb_id)})
    await knowledge_bases_collection.delete_one({"_id": ObjectId(kb_id)})

    # Delete Qdrant collection
    delete_collection(kb_id)

    return {"detail": "Knowledge base deleted"}
