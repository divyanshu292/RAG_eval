from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int = 0
    status: str = "processing"
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict) -> "DocumentResponse":
        return cls(
            id=str(doc["_id"]),
            knowledge_base_id=str(doc["knowledge_base_id"]),
            filename=doc["filename"],
            file_type=doc["file_type"],
            file_size_bytes=doc["file_size_bytes"],
            chunk_count=doc.get("chunk_count", 0),
            status=doc.get("status", "processing"),
            created_at=doc["created_at"],
        )
