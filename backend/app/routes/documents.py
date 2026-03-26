from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from app.database import chunks_collection, documents_collection, knowledge_bases_collection
from app.models.document import DocumentResponse
from app.services.chunker import chunk_text
from app.services.document_processor import extract_text
from app.services.embedder import embed_texts
from app.services.retriever import upsert_vectors, delete_vectors_by_document
from app.utils.file_utils import get_file_type, MAX_FILE_SIZE

router = APIRouter(tags=["Documents"])


async def _process_document(document_id: str, kb_id: str, file_bytes: bytes, file_type: str, filename: str):
    try:
        # 1. Parse document
        raw_text = extract_text(file_bytes, file_type)
        if not raw_text.strip():
            await documents_collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": "failed"}},
            )
            return

        # 2. Chunk text
        chunks = chunk_text(raw_text, source_filename=filename)

        # 3. Embed all chunks
        texts = [c["text"] for c in chunks]
        # Batch embeddings in groups of 100
        all_embeddings = []
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            embeddings = await embed_texts(batch)
            all_embeddings.extend(embeddings)

        # 4. Store chunks in MongoDB
        chunk_docs = []
        for chunk in chunks:
            chunk_docs.append(
                {
                    "document_id": ObjectId(document_id),
                    "knowledge_base_id": ObjectId(kb_id),
                    "text": chunk["text"],
                    "chunk_index": chunk["chunk_index"],
                    "metadata": chunk["metadata"],
                }
            )
        if chunk_docs:
            result = await chunks_collection.insert_many(chunk_docs)
            chunk_ids = [str(cid) for cid in result.inserted_ids]

            # 5. Store vectors in Qdrant
            payloads = [
                {"document_id": document_id, "chunk_index": c["chunk_index"]}
                for c in chunks
            ]
            upsert_vectors(kb_id, chunk_ids, all_embeddings, payloads)

        # 6. Update document status
        await documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "ready", "chunk_count": len(chunks)}},
        )
        await knowledge_bases_collection.update_one(
            {"_id": ObjectId(kb_id)},
            {"$inc": {"document_count": 1}},
        )

    except Exception:
        await documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "failed"}},
        )


@router.post("/knowledge-bases/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(kb_id: str, file: UploadFile, background_tasks: BackgroundTasks):
    # Validate KB exists
    kb = await knowledge_bases_collection.find_one({"_id": ObjectId(kb_id)})
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Validate file type
    file_type = get_file_type(file.filename or "")
    if not file_type:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50 MB.")

    # Create document record
    doc = {
        "knowledge_base_id": ObjectId(kb_id),
        "filename": file.filename,
        "file_type": file_type,
        "file_size_bytes": len(file_bytes),
        "chunk_count": 0,
        "status": "processing",
        "created_at": datetime.now(timezone.utc),
    }
    result = await documents_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Process in background
    background_tasks.add_task(
        _process_document,
        str(result.inserted_id),
        kb_id,
        file_bytes,
        file_type,
        file.filename,
    )

    return DocumentResponse.from_mongo(doc)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(kb_id: str):
    cursor = documents_collection.find({"knowledge_base_id": ObjectId(kb_id)}).sort("created_at", -1)
    return [DocumentResponse.from_mongo(doc) async for doc in cursor]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    doc = await documents_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    kb_id = str(doc["knowledge_base_id"])

    # Delete chunks from MongoDB
    await chunks_collection.delete_many({"document_id": ObjectId(doc_id)})

    # Delete vectors from Qdrant
    delete_vectors_by_document(kb_id, doc_id)

    # Delete document
    await documents_collection.delete_one({"_id": ObjectId(doc_id)})

    # Decrement document count
    await knowledge_bases_collection.update_one(
        {"_id": ObjectId(kb_id)},
        {"$inc": {"document_count": -1}},
    )

    return {"detail": "Document deleted"}
