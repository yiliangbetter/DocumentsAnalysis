"""Tests for graph sidecar storage."""
from pathlib import Path

from core.document import DocumentChunk
from storage.graph_store import GraphStore


class TestGraphStore:
    """Test cases for GraphStore."""

    def test_upsert_document_chunks_creates_graph_file(self, tmp_path: Path):
        store = GraphStore(storage_path=tmp_path)
        chunks = [
            DocumentChunk(
                id="chunk-1",
                document_id="doc-1",
                text="Alice met Bob in Paris.",
                chunk_index=0,
                start_char=0,
                end_char=24,
                metadata={
                    "entities": ["Alice", "Bob", "Paris"],
                    "entity_confidence": {"Alice": 0.7, "Bob": 0.7, "Paris": 0.65},
                },
            )
        ]

        store.upsert_document_chunks("doc-1", chunks)

        graph_file = tmp_path / "doc-1.json"
        assert graph_file.exists()
        graph = graph_file.read_text(encoding="utf-8")
        assert "chunk_in_document" in graph
        assert "mentions" in graph
        assert "entity:alice" in graph

    def test_delete_by_document_id(self, tmp_path: Path):
        store = GraphStore(storage_path=tmp_path)
        chunks = [
            DocumentChunk(
                id="chunk-1",
                document_id="doc-1",
                text="Alice met Bob in Paris.",
                chunk_index=0,
                start_char=0,
                end_char=24,
                metadata={"entities": ["Alice"], "entity_confidence": {"Alice": 0.7}},
            )
        ]
        store.upsert_document_chunks("doc-1", chunks)

        assert store.delete_by_document_id("doc-1") is True
        assert store.delete_by_document_id("doc-1") is False
