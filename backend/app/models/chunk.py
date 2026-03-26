from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    page_number: int | None = None
    source_filename: str = ""


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    knowledge_base_id: str
    text: str
    chunk_index: int
    metadata: ChunkMetadata

    @classmethod
    def from_mongo(cls, doc: dict) -> "ChunkResponse":
        return cls(
            id=str(doc["_id"]),
            document_id=str(doc["document_id"]),
            knowledge_base_id=str(doc["knowledge_base_id"]),
            text=doc["text"],
            chunk_index=doc["chunk_index"],
            metadata=ChunkMetadata(**doc.get("metadata", {})),
        )
