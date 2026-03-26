from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import knowledge_bases, documents, query, analytics

app = FastAPI(title="RAG Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge_bases.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
