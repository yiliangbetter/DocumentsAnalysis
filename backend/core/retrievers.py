"""Retriever abstractions for RAG query-time chunk selection."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from storage.vector_store import VectorStore


RetrievedChunk = Tuple[str, float, str]


class BaseRetriever(ABC):
    """Retrieval interface used by the RAG pipeline."""

    @abstractmethod
    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Return relevant chunks as (chunk_id, score, text)."""


class VectorRetriever(BaseRetriever):
    """Vector-only retriever backed by the existing Chroma store."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )


class HybridRetriever(BaseRetriever):
    """Hybrid retriever scaffold (vector first, graph augmentation later)."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        # Phase-1 hybrid rollout keeps vector behavior stable.
        # Graph expansion/reranking will be added in a follow-up step.
        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )


def build_retriever(mode: str, vector_store: VectorStore) -> BaseRetriever:
    """Create a retriever for the configured mode."""
    normalized_mode = (mode or "vector").strip().lower()
    if normalized_mode == "hybrid":
        return HybridRetriever(vector_store)
    # `graph` currently falls back to vector until graph-only retrieval is implemented.
    return VectorRetriever(vector_store)
