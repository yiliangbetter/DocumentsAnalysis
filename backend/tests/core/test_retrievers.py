"""Tests for hybrid and graph retriever behavior."""
from unittest.mock import MagicMock

from core.retrievers import GraphRetriever, HybridRetriever


class TestHybridRetriever:
    """Hybrid retrieval merge and ranking tests."""

    def test_hybrid_merges_vector_and_graph_candidates(self):
        vector_store = MagicMock()
        graph_store = MagicMock()

        vector_store.search.return_value = [
            ("c1", 0.91, "seed chunk"),
            ("c2", 0.82, "second chunk"),
        ]
        graph_store.expand_related_chunks.return_value = [("c3", 0.95)]
        vector_store.get_chunks_by_ids.return_value = [("c3", "graph expanded chunk")]

        retriever = HybridRetriever(vector_store=vector_store, graph_store=graph_store)
        results = retriever.retrieve(query_embedding=[0.1, 0.2], top_k=3)

        returned_ids = [chunk_id for chunk_id, _, _ in results]
        assert "c1" in returned_ids
        assert "c3" in returned_ids
        assert len(results) == 3

    def test_hybrid_falls_back_to_vector_without_graph(self):
        vector_store = MagicMock()
        vector_store.search.return_value = [("c1", 0.7, "only vector")]

        retriever = HybridRetriever(vector_store=vector_store, graph_store=None)
        results = retriever.retrieve(query_embedding=[0.1], top_k=1)

        assert results == [("c1", 0.7, "only vector")]


class TestGraphRetriever:
    """Graph-prioritized retrieval tests."""

    def test_graph_retriever_prioritizes_graph_expansion(self):
        vector_store = MagicMock()
        graph_store = MagicMock()
        vector_store.search.return_value = [
            ("c1", 0.88, "seed 1"),
            ("c2", 0.76, "seed 2"),
        ]
        graph_store.expand_related_chunks.return_value = [("c3", 0.95), ("c4", 0.7)]
        vector_store.get_chunks_by_ids.return_value = [
            ("c3", "graph 3"),
            ("c4", "graph 4"),
        ]

        retriever = GraphRetriever(vector_store=vector_store, graph_store=graph_store)
        results = retriever.retrieve(query_embedding=[0.1, 0.3], top_k=2)

        assert [r[0] for r in results] == ["c3", "c4"]
