"""System API routes."""
from fastapi import APIRouter, Depends

from api.dependencies import get_document_store, get_vector_store
from config import settings
from storage.document_store import DocumentStore
from storage.vector_store import VectorStore

router = APIRouter()


@router.get("/stats")
async def get_stats(
    document_store: DocumentStore = Depends(get_document_store),
    vector_store: VectorStore = Depends(get_vector_store),
):
    """Get system statistics."""
    status_counts = document_store.count_by_status()

    return {
        "documents": {
            "total": document_store.count(),
            "by_status": status_counts,
        },
        "chunks": {
            "total": vector_store.get_chunk_count(),
        },
        "storage": {
            "vector_db_path": str(settings.VECTOR_DB_PATH),
            "document_store_path": str(settings.DOCUMENT_STORE_PATH),
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
