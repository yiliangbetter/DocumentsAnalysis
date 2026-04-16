"""FastAPI dependency injection utilities."""
from typing import Annotated

from fastapi import Depends

from storage.document_store import DocumentStore
from storage.vector_store import VectorStore


async def get_document_store() -> DocumentStore:
    """Dependency to get the document store instance."""
    # Import here to avoid circular imports
    from main import document_store

    if document_store is None:
        raise RuntimeError("Document store not initialized")
    return document_store


async def get_vector_store() -> VectorStore:
    """Dependency to get the vector store instance."""
    # Import here to avoid circular imports
    from main import vector_store

    if vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return vector_store


# Dependency injection types
DocumentStoreDep = Annotated[DocumentStore, Depends(get_document_store)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store)]
