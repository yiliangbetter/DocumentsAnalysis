"""Retriever abstractions for RAG query-time chunk selection."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from storage.graph_store import GraphStore
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
    """Hybrid retriever: vector recall + graph expansion rerank."""

    def __init__(self, vector_store: VectorStore, graph_store: Optional[GraphStore] = None):
        self.vector_store = vector_store
        self.graph_store = graph_store

    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
        if not vector_results or self.graph_store is None:
            return vector_results

        seed_chunk_ids = [chunk_id for chunk_id, _, _ in vector_results]
        related = self.graph_store.expand_related_chunks(seed_chunk_ids, limit=top_k * 2)
        if not related:
            return vector_results

        related_scores = {chunk_id: relation_score for chunk_id, relation_score in related}
        fetched = self.vector_store.get_chunks_by_ids(
            list(related_scores.keys()),
            document_ids=document_ids,
        )
        if not fetched:
            return vector_results

        max_vector_score = max(score for _, score, _ in vector_results)
        merged: Dict[str, RetrievedChunk] = {
            chunk_id: (chunk_id, score, text) for chunk_id, score, text in vector_results
        }
        for chunk_id, text in fetched:
            relation_score = related_scores.get(chunk_id, 0.0)
            hybrid_score = (max_vector_score * 0.85) + (relation_score * 0.15)
            current = merged.get(chunk_id)
            if current is None or hybrid_score > current[1]:
                merged[chunk_id] = (chunk_id, hybrid_score, text)

        return sorted(merged.values(), key=lambda item: item[1], reverse=True)[:top_k]


def build_retriever(
    mode: str,
    vector_store: VectorStore,
    graph_store: Optional[GraphStore] = None,
) -> BaseRetriever:
    """Create a retriever for the configured mode."""
    normalized_mode = (mode or "vector").strip().lower()
    if normalized_mode == "hybrid":
        return HybridRetriever(vector_store, graph_store=graph_store)
    # `graph` currently falls back to vector until graph-only retrieval is implemented.
    return VectorRetriever(vector_store)
