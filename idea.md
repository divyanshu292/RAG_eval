# RAG Service — Implementation Plan

## Context
Build a RAG-as-a-service where users upload documents (PDF, DOCX, TXT), create isolated knowledge bases, and query them using natural language. Key differentiator: built-in evaluation pipeline tracking retrieval precision, answer faithfulness, and hallucination rates. Stack: FastAPI + MongoDB + OpenAI + Streamlit. No auth — open access, designed for easy local/self-hosted use.

---

## Local Setup (for anyone who clones the repo)

**Prerequisites**: Docker, an OpenAI API key

```bash
git clone <repo>
cd RAG_service
cp .env.example .env           # fill in OPENAI_API_KEY
docker compose up --build      # starts MongoDB + Qdrant + backend + frontend
```

That's it. Opens at `localhost:8501`.

### `.env.example`
```env
# OpenAI (only thing you need to set)
OPENAI_API_KEY=sk-...

# Services (no changes needed for local dev)
MONGODB_URI=mongodb://mongodb:27017/rag_service
QDRANT_URL=http://qdrant:6333
BACKEND_URL=http://backend:8000
```

### `docker-compose.yml` services
| Service | Image | Port |
|---------|-------|------|
| `mongodb` | `mongo:7` | 27017 |
| `qdrant` | `qdrant/qdrant:latest` | 6333 |
| `backend` | Built from `backend/Dockerfile` | 8000 |
| `frontend` | Built from `frontend/Dockerfile` | 8501 |

---

## Project Structure

```
RAG_service/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings (env vars, OpenAI keys, MongoDB URI)
│   │   ├── database.py              # MongoDB + Qdrant connection setup
│   │   ├── models/
│   │   │   ├── knowledge_base.py    # Knowledge base schema
│   │   │   ├── document.py          # Document metadata schema
│   │   │   ├── chunk.py             # Chunk schema
│   │   │   └── query.py             # Query + evaluation metrics schema
│   │   ├── routes/
│   │   │   ├── knowledge_bases.py   # CRUD knowledge bases
│   │   │   ├── documents.py         # Upload, list, delete documents
│   │   │   ├── query.py             # Query a knowledge base
│   │   │   └── analytics.py         # Evaluation metrics & dashboard data
│   │   ├── services/
│   │   │   ├── document_processor.py # Parse PDF/DOCX/TXT → raw text
│   │   │   ├── chunker.py           # Split text into chunks (recursive, 512 tokens, 50 overlap)
│   │   │   ├── embedder.py          # OpenAI text-embedding-3-small
│   │   │   ├── retriever.py         # Qdrant vector search
│   │   │   ├── generator.py         # GPT-4o-mini for answer generation
│   │   │   └── evaluator.py         # Evaluation pipeline (faithfulness, relevance, hallucination)
│   │   └── utils/
│   │       └── file_utils.py        # File type detection, temp storage
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                       # Streamlit app entry point
│   ├── pages/
│   │   ├── 1_Knowledge_Bases.py     # Create, list, select KB
│   │   ├── 2_Upload_Documents.py    # Upload files to selected KB
│   │   ├── 3_Chat.py                # Query interface with chat history
│   │   └── 4_Analytics.py           # Evaluation metrics dashboard
│   ├── lib/
│   │   └── api.py                   # Backend API client (requests wrapper)
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml               # backend + frontend + mongo + qdrant
├── .env.example                     # all required env vars with comments
├── README.md                        # setup guide
└── idea.md
```

---

## MongoDB Collections

### `knowledge_bases`
```json
{
  "_id": "ObjectId",
  "name": "string",
  "description": "string",
  "document_count": 0,
  "created_at": "datetime"
}
```

### `documents`
```json
{
  "_id": "ObjectId",
  "knowledge_base_id": "ObjectId",
  "filename": "string",
  "file_type": "pdf | docx | txt",
  "file_size_bytes": 0,
  "chunk_count": 0,
  "status": "processing | ready | failed",
  "created_at": "datetime"
}
```

### `chunks` (MongoDB — text + metadata only)
```json
{
  "_id": "ObjectId",
  "document_id": "ObjectId",
  "knowledge_base_id": "ObjectId",
  "text": "string",
  "chunk_index": 0,
  "metadata": {
    "page_number": 1,
    "source_filename": "string"
  }
}
```

### Vector Store (Qdrant — runs locally in Docker)
- One **Qdrant collection per knowledge base** (named `kb_{knowledge_base_id}`)
- Each point: `id` = chunk's MongoDB `_id`, `vector` = 1536-dim embedding, `payload` = `{ document_id, chunk_index }`
- Qdrant handles similarity search — no cloud account needed, runs at `localhost:6333`

### `queries`
```json
{
  "_id": "ObjectId",
  "knowledge_base_id": "ObjectId",
  "question": "string",
  "answer": "string",
  "retrieved_chunks": ["ObjectId", ...],
  "evaluation": {
    "retrieval_relevance": 0.85,    // How relevant are retrieved chunks to the question
    "answer_faithfulness": 0.92,    // Does the answer stick to retrieved context
    "hallucination_score": 0.08     // How much of the answer is unsupported by context
  },
  "latency_ms": 1200,
  "created_at": "datetime"
}
```

---

## API Endpoints

### Knowledge Bases
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/knowledge-bases` | Create a KB |
| GET | `/api/knowledge-bases` | List all KBs |
| GET | `/api/knowledge-bases/{id}` | Get KB details |
| DELETE | `/api/knowledge-bases/{id}` | Delete KB + all its data |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/knowledge-bases/{id}/documents` | Upload file(s) |
| GET | `/api/knowledge-bases/{id}/documents` | List documents in KB |
| DELETE | `/api/documents/{id}` | Delete document + chunks |

### Query
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/knowledge-bases/{id}/query` | Ask a question |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/knowledge-bases/{id}/analytics` | Avg scores, query count, trends |
| GET | `/api/knowledge-bases/{id}/queries` | Query history with eval scores |

---

## Core Pipelines

### 1. Document Ingestion Pipeline
```
Upload file → Detect type → Parse to text → Chunk (512 tokens, 50 overlap) → Embed via OpenAI → Store text in MongoDB + vectors in Qdrant
```
- **Parsing**: `pdfplumber` for PDF, `python-docx` for DOCX, plain read for TXT
- **Chunking**: Recursive character text splitter (langchain), 512 tokens, 50 token overlap
- **Embedding**: OpenAI `text-embedding-3-small` (1536 dims, cheap, fast)
- **Processing**: Run as background task (`fastapi.BackgroundTasks`) so upload returns immediately

### 2. Query Pipeline
```
Question → Embed question → Qdrant search (top-k=5 from KB collection) → Fetch chunk text from MongoDB → Build prompt with retrieved chunks → GPT-4o-mini generates answer → Evaluate → Store & return
```

### 3. Evaluation Pipeline (runs on every query)
Three metrics, each scored 0.0 → 1.0:

**Retrieval Relevance** — Are the retrieved chunks relevant to the question?
- Send to GPT-4o-mini: "Rate how relevant each chunk is to this question on 0-1 scale"
- Average the scores

**Answer Faithfulness** — Is the answer grounded in the retrieved chunks?
- Send to GPT-4o-mini: "Given these source chunks and this answer, what fraction of claims in the answer are supported by the sources?"
- Returns a 0-1 score

**Hallucination Score** — What fraction of the answer is NOT supported?
- `1.0 - faithfulness` (inverse, but computed independently for nuance)
- Send to GPT-4o-mini: "Identify claims in the answer not supported by the sources. What fraction of the answer is unsupported?"

All three use a cheap LLM-as-judge approach with structured output.

---

## Key Libraries

### Backend
```
fastapi
uvicorn
motor              # async MongoDB driver
pymongo
openai
qdrant-client      # vector store client
pdfplumber         # PDF parsing
python-docx        # DOCX parsing
langchain-text-splitters  # text chunking
python-multipart   # file uploads
pydantic-settings  # config management
```

### Frontend
```
streamlit          # UI framework
requests           # backend API calls
plotly             # analytics charts (works natively with Streamlit)
```

---

## Implementation Phases

### Phase 1 — Project Setup & Infrastructure
1. Docker Compose (MongoDB + Qdrant + backend + frontend) — `docker compose up` runs everything
2. `.env.example` with all required vars
3. Backend scaffolding: FastAPI app, config, MongoDB + Qdrant connections

### Phase 2 — Core Backend
4. Knowledge base CRUD endpoints
5. File upload endpoint + parsing (PDF, DOCX, TXT)
6. Chunking service
7. OpenAI embedding service
8. Store chunks in MongoDB + vectors in Qdrant

### Phase 3 — Query Pipeline
9. Query embedding + Qdrant vector search retrieval
10. LLM answer generation with retrieved context
11. Full query endpoint

### Phase 4 — Evaluation Pipeline
12. Retrieval relevance scorer
13. Answer faithfulness scorer
14. Hallucination detector
15. Store metrics with each query

### Phase 5 — Streamlit Frontend
16. Streamlit app scaffolding + sidebar navigation
17. Knowledge Bases page (create, list, select)
18. Upload Documents page (file uploader, processing status)
19. Chat page (query interface with chat history)
20. Analytics page (evaluation metrics with Plotly charts)

### Phase 6 — Polish
21. Error handling, loading states, edge cases
22. File size limits
23. README with setup guide

---

## Verification
- Upload a multi-page PDF → confirm chunks appear in MongoDB with embeddings
- Query the KB → confirm relevant chunks retrieved and coherent answer returned
- Check `queries` collection → confirm evaluation scores are present and reasonable
- Analytics endpoint → returns aggregated metrics
- Frontend → full flow works: create KB → upload → chat → view analytics
