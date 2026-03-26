from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class EvaluationMetrics(BaseModel):
    retrieval_relevance: float = 0.0
    answer_faithfulness: float = 0.0
    hallucination_score: float = 0.0


class QueryResponse(BaseModel):
    id: str
    knowledge_base_id: str
    question: str
    answer: str
    retrieved_chunks: list[str]
    evaluation: EvaluationMetrics
    latency_ms: int
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict) -> "QueryResponse":
        return cls(
            id=str(doc["_id"]),
            knowledge_base_id=str(doc["knowledge_base_id"]),
            question=doc["question"],
            answer=doc["answer"],
            retrieved_chunks=[str(c) for c in doc.get("retrieved_chunks", [])],
            evaluation=EvaluationMetrics(**doc.get("evaluation", {})),
            latency_ms=doc.get("latency_ms", 0),
            created_at=doc["created_at"],
        )
