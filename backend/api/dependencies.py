"""Shared FastAPI dependencies for application stores."""
from typing import Optional

from fastapi import HTTPException, Request

from storage.document_store import DocumentStore
from storage.graph_store import GraphStore
from storage.vector_store import VectorStore


def _missing_store(detail: str) -> HTTPException:
    return HTTPException(status_code=503, detail=detail)


def get_document_store(request: Request) -> DocumentStore:
    store = getattr(request.app.state, "document_store", None)
    if store is None:
        raise _missing_store("Document store not initialized")
    return store


def get_vector_store(request: Request) -> VectorStore:
    store = getattr(request.app.state, "vector_store", None)
    if store is None:
        raise _missing_store("Vector store not initialized")
    return store


def get_graph_store(request: Request) -> Optional[GraphStore]:
    return getattr(request.app.state, "graph_store", None)
