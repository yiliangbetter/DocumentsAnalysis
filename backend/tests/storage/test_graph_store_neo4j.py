"""Tests for Neo4j-backed graph store behavior."""
from core.document import DocumentChunk
from storage.graph_store import GraphStore


class _FakeCounters:
    def __init__(self, nodes_deleted: int = 0):
        self.nodes_deleted = nodes_deleted


class _FakeSummary:
    def __init__(self, nodes_deleted: int = 0):
        self.counters = _FakeCounters(nodes_deleted=nodes_deleted)


class _FakeResult:
    def __init__(self, rows=None, single_row=None, nodes_deleted: int = 0):
        self._rows = rows or []
        self._single_row = single_row
        self._nodes_deleted = nodes_deleted

    def __iter__(self):
        return iter(self._rows)

    def single(self):
        return self._single_row

    def consume(self):
        return _FakeSummary(nodes_deleted=self._nodes_deleted)


class _FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query, **params):
        self.calls.append((query, params))
        return self.responses.pop(0)


class _FakeDriver:
    def __init__(self, responses):
        self._session = _FakeSession(responses)

    def session(self, database=None):  # noqa: ARG002
        return self._session


def test_upsert_document_chunks_uses_neo4j_driver(tmp_path):
    driver = _FakeDriver([_FakeResult()])
    store = GraphStore(storage_path=tmp_path, driver=driver)

    chunks = [
        DocumentChunk(
            id="chunk-1",
            document_id="doc-1",
            text="Alice met Bob in Paris.",
            chunk_index=0,
            start_char=0,
            end_char=24,
            metadata={
                "entities": ["Alice", "Paris"],
                "entity_confidence": {"Alice": 0.8, "Paris": 0.7},
            },
        )
    ]
    store.upsert_document_chunks("doc-1", chunks)

    assert len(driver._session.calls) == 1
    _, params = driver._session.calls[0]
    assert params["document_id"] == "doc-1"
    assert params["chunks"][0]["id"] == "chunk-1"


def test_expand_related_chunks_with_neo4j_driver(tmp_path):
    rows = [{"chunk_id": "c2", "relation_score": 0.63}, {"chunk_id": "c4", "relation_score": 0.5}]
    driver = _FakeDriver([_FakeResult(rows=rows)])
    store = GraphStore(storage_path=tmp_path, driver=driver)

    expanded = store.expand_related_chunks(["c1"], limit=5)
    assert expanded == [("c2", 0.63), ("c4", 0.5)]


def test_get_stats_and_delete_with_neo4j_driver(tmp_path):
    driver = _FakeDriver(
        [
            _FakeResult(single_row={"documents_indexed": 3}),
            _FakeResult(nodes_deleted=2),
            _FakeResult(),
        ]
    )
    store = GraphStore(storage_path=tmp_path, driver=driver)

    assert store.get_stats() == {"documents_indexed": 3}
    assert store.delete_by_document_id("doc-1") is True
