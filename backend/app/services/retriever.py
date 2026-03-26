import uuid

from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.database import qdrant_client


def _oid_to_uuid(oid: str) -> str:
    """Convert 24-char MongoDB ObjectId hex to a valid UUID for Qdrant."""
    return str(uuid.UUID("00000000" + oid))


def _uuid_to_oid(uuid_str: str) -> str:
    """Convert UUID back to MongoDB ObjectId hex."""
    return uuid_str.replace("-", "")[8:]


def get_collection_name(kb_id: str) -> str:
    return f"kb_{kb_id}"


def ensure_collection(kb_id: str) -> None:
    collection_name = get_collection_name(kb_id)
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name not in collections:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )


def upsert_vectors(kb_id: str, chunk_ids: list[str], embeddings: list[list[float]], payloads: list[dict]) -> None:
    collection_name = get_collection_name(kb_id)
    ensure_collection(kb_id)
    points = [
        PointStruct(
            id=_oid_to_uuid(chunk_id),
            vector=embedding,
            payload={**payload, "mongo_id": chunk_id},
        )
        for chunk_id, embedding, payload in zip(chunk_ids, embeddings, payloads)
    ]
    qdrant_client.upsert(collection_name=collection_name, points=points)


def search_vectors(kb_id: str, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    collection_name = get_collection_name(kb_id)
    if top_k is None:
        top_k = settings.top_k
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
    )
    return [
        {
            "chunk_id": hit.payload.get("mongo_id", _uuid_to_oid(str(hit.id))),
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]


def delete_collection(kb_id: str) -> None:
    collection_name = get_collection_name(kb_id)
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name in collections:
        qdrant_client.delete_collection(collection_name=collection_name)


def delete_vectors_by_document(kb_id: str, document_id: str) -> None:
    collection_name = get_collection_name(kb_id)
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    qdrant_client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]
        ),
    )
