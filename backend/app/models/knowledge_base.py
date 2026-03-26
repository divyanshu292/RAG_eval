from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str
    document_count: int = 0
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict) -> "KnowledgeBaseResponse":
        return cls(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description", ""),
            document_count=doc.get("document_count", 0),
            created_at=doc["created_at"],
        )
