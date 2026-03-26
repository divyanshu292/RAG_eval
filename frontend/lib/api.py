import os

import requests

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BASE_URL}{path}"


# Knowledge Bases
def create_knowledge_base(name: str, description: str = "") -> dict:
    r = requests.post(_url("/api/knowledge-bases"), json={"name": name, "description": description})
    r.raise_for_status()
    return r.json()


def list_knowledge_bases() -> list[dict]:
    r = requests.get(_url("/api/knowledge-bases"))
    r.raise_for_status()
    return r.json()


def get_knowledge_base(kb_id: str) -> dict:
    r = requests.get(_url(f"/api/knowledge-bases/{kb_id}"))
    r.raise_for_status()
    return r.json()


def delete_knowledge_base(kb_id: str) -> dict:
    r = requests.delete(_url(f"/api/knowledge-bases/{kb_id}"))
    r.raise_for_status()
    return r.json()


# Documents
def upload_document(kb_id: str, file) -> dict:
    r = requests.post(
        _url(f"/api/knowledge-bases/{kb_id}/documents"),
        files={"file": (file.name, file.getvalue(), file.type)},
    )
    r.raise_for_status()
    return r.json()


def list_documents(kb_id: str) -> list[dict]:
    r = requests.get(_url(f"/api/knowledge-bases/{kb_id}/documents"))
    r.raise_for_status()
    return r.json()


def delete_document(doc_id: str) -> dict:
    r = requests.delete(_url(f"/api/documents/{doc_id}"))
    r.raise_for_status()
    return r.json()


# Query
def query_knowledge_base(kb_id: str, question: str) -> dict:
    r = requests.post(_url(f"/api/knowledge-bases/{kb_id}/query"), json={"question": question})
    r.raise_for_status()
    return r.json()


# Analytics
def get_analytics(kb_id: str) -> dict:
    r = requests.get(_url(f"/api/knowledge-bases/{kb_id}/analytics"))
    r.raise_for_status()
    return r.json()


def get_query_history(kb_id: str) -> list[dict]:
    r = requests.get(_url(f"/api/knowledge-bases/{kb_id}/queries"))
    r.raise_for_status()
    return r.json()
