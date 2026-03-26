# RAG Service

A full-stack Retrieval-Augmented Generation (RAG) app with:
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Vector DB:** Qdrant
- **Metadata DB:** MongoDB
- **LLM/Embeddings:** OpenAI API

## Features

- Create and manage knowledge bases
- Upload and process documents
- Chunk, embed, and store vectors in Qdrant
- Ask questions over uploaded knowledge
- Basic analytics dashboard

## Tech Stack

- Python 3.12
- FastAPI + Uvicorn
- Streamlit
- MongoDB
- Qdrant
- OpenAI SDK

## Project Structure

```text
RAG_service/
  backend/            # FastAPI API + ingestion/retrieval services
  frontend/           # Streamlit UI
  docker-compose.yml  # Full local stack orchestration
  .env.example        # Environment template
```

## Prerequisites

- Docker + Docker Compose
- OpenAI API key

## Environment Setup

1. Copy the env template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and set:
   - `OPENAI_API_KEY`

`MONGODB_URI`, `QDRANT_URL`, and `BACKEND_URL` defaults are already set for local Docker usage.

## Run with Docker (Recommended)

From project root:

```bash
docker compose up --build
```

Services:
- Frontend (Streamlit): `http://localhost:8501`
- Backend (FastAPI): `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Qdrant: `http://localhost:6333`
- MongoDB: `mongodb://localhost:27017`

To stop:

```bash
docker compose down
```

## Run Locally (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

In a new terminal:

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## API Notes

- API routers are mounted under `/api`
- Service health endpoint is `/health`

## Security

- Do not commit `.env`
- Keep API keys only in local environment variables or secret managers
- `.gitignore` is configured to exclude local secret files
