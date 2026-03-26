from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database import knowledge_bases_collection, queries_collection
from app.models.query import QueryResponse

router = APIRouter(tags=["Analytics"])


@router.get("/knowledge-bases/{kb_id}/analytics")
async def get_analytics(kb_id: str):
    kb = await knowledge_bases_collection.find_one({"_id": ObjectId(kb_id)})
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    pipeline = [
        {"$match": {"knowledge_base_id": ObjectId(kb_id)}},
        {
            "$group": {
                "_id": None,
                "total_queries": {"$sum": 1},
                "avg_retrieval_relevance": {"$avg": "$evaluation.retrieval_relevance"},
                "avg_answer_faithfulness": {"$avg": "$evaluation.answer_faithfulness"},
                "avg_hallucination_score": {"$avg": "$evaluation.hallucination_score"},
                "avg_latency_ms": {"$avg": "$latency_ms"},
            }
        },
    ]
    results = await queries_collection.aggregate(pipeline).to_list(1)

    if not results:
        return {
            "total_queries": 0,
            "avg_retrieval_relevance": 0.0,
            "avg_answer_faithfulness": 0.0,
            "avg_hallucination_score": 0.0,
            "avg_latency_ms": 0.0,
        }

    data = results[0]
    data.pop("_id", None)
    # Round averages
    for key in ["avg_retrieval_relevance", "avg_answer_faithfulness", "avg_hallucination_score", "avg_latency_ms"]:
        if data.get(key) is not None:
            data[key] = round(data[key], 3)
    return data


@router.get("/knowledge-bases/{kb_id}/queries", response_model=list[QueryResponse])
async def get_query_history(kb_id: str):
    cursor = queries_collection.find({"knowledge_base_id": ObjectId(kb_id)}).sort("created_at", -1)
    return [QueryResponse.from_mongo(doc) async for doc in cursor]
