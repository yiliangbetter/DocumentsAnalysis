"""System API routes."""
from fastapi import APIRouter

from config import settings
from main import document_store, vector_store

router = APIRouter()


@router.get("/stats")
async def get_stats():
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
