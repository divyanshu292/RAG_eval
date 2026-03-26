import time
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database import chunks_collection, knowledge_bases_collection, queries_collection
from app.models.query import QueryRequest, QueryResponse
from app.services.embedder import embed_query
from app.services.evaluator import evaluate_query
from app.services.generator import generate_answer
from app.services.retriever import search_vectors

router = APIRouter(tags=["Query"])


@router.post("/knowledge-bases/{kb_id}/query", response_model=QueryResponse)
async def query_knowledge_base(kb_id: str, req: QueryRequest):
    start = time.time()

    # Validate KB
    kb = await knowledge_bases_collection.find_one({"_id": ObjectId(kb_id)})
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 1. Embed question
    query_embedding = await embed_query(req.question)

    # 2. Search Qdrant
    results = search_vectors(kb_id, query_embedding)
    if not results:
        raise HTTPException(status_code=404, detail="No relevant chunks found. Upload documents first.")

    # 3. Fetch chunk texts from MongoDB
    chunk_ids = [ObjectId(r["chunk_id"]) for r in results]
    chunk_docs = []
    async for doc in chunks_collection.find({"_id": {"$in": chunk_ids}}):
        chunk_docs.append(doc)

    # Sort by chunk_index for coherent context
    chunk_docs.sort(key=lambda d: d.get("chunk_index", 0))

    chunks_for_context = [
        {
            "text": doc["text"],
            "chunk_index": doc.get("chunk_index", 0),
            "metadata": doc.get("metadata", {}),
        }
        for doc in chunk_docs
    ]

    # 4. Generate answer
    answer = await generate_answer(req.question, chunks_for_context)

    # 5. Evaluate
    evaluation = await evaluate_query(req.question, answer, chunks_for_context)

    latency_ms = int((time.time() - start) * 1000)

    # 6. Store query
    query_doc = {
        "knowledge_base_id": ObjectId(kb_id),
        "question": req.question,
        "answer": answer,
        "retrieved_chunks": [doc["_id"] for doc in chunk_docs],
        "evaluation": evaluation,
        "latency_ms": latency_ms,
        "created_at": datetime.now(timezone.utc),
    }
    result = await queries_collection.insert_one(query_doc)
    query_doc["_id"] = result.inserted_id

    return QueryResponse.from_mongo(query_doc)
