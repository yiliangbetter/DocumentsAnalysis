"""Tests for query API routes."""
from unittest.mock import MagicMock, patch

from api.query import get_rag_pipeline


def _override_rag_pipeline(test_client, pipeline):
    test_client.app.dependency_overrides[get_rag_pipeline] = lambda: pipeline


def _clear_override(test_client):
    test_client.app.dependency_overrides.pop(get_rag_pipeline, None)


class TestQueryEndpoint:
    """Test cases for /api/query endpoint."""

    def test_query_success(self, test_client, mock_kimi_client):
        """Test successful query with valid data."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.return_value = {
                "answer": "Test answer",
                "sources": [
                    {"chunk_id": "chunk-1", "score": 0.95, "text": "Source text"}
                ],
                "confidence": 0.95,
                "context_used": 1,
            }

            response = test_client.post(
                "/api/query",
                json={
                    "question": "What is the test question?",
                    "top_k": 5,
                    "document_ids": ["doc-1", "doc-2"],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test answer"
            assert len(data["sources"]) == 1
            assert data["confidence"] == 0.95
        finally:
            _clear_override(test_client)

    def test_query_missing_question(self, test_client):
        """Test query without question field."""
        response = test_client.post(
            "/api/query",
            json={},
        )

        assert response.status_code == 422  # Validation error

    def test_query_empty_question(self, test_client):
        """Test query with empty question."""
        response = test_client.post(
            "/api/query",
            json={"question": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_query_error_handling(self, test_client):
        """Test error handling in query."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.return_value = {
                "answer": "Error occurred",
                "sources": [],
                "confidence": 0.0,
                "error": "Some error",
            }

            response = test_client.post(
                "/api/query",
                json={"question": "Test question"},
            )

            assert response.status_code == 500
        finally:
            _clear_override(test_client)

    def test_query_exception_handling(self, test_client):
        """Test exception handling in query."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.side_effect = Exception("Unexpected error")

            response = test_client.post(
                "/api/query",
                json={"question": "Test question"},
            )

            assert response.status_code == 500
        finally:
            _clear_override(test_client)


class TestSearchEndpoint:
    """Test cases for /api/search endpoint."""

    def test_search_success(self, test_client):
        """Test successful search with valid data."""
        mock_store = test_client.app.state.vector_store
        with patch("storage.vector_store.EmbeddingGenerator") as mock_embedder:
            mock_instance = MagicMock()
            mock_instance.embed_text.return_value = [0.1] * 384
            mock_embedder.return_value = mock_instance

            mock_store.search.return_value = [
                ("chunk-1", 0.95, "Test result 1"),
                ("chunk-2", 0.85, "Test result 2"),
            ]

            response = test_client.post(
                "/api/search",
                json={
                    "query": "test query",
                    "top_k": 5,
                    "document_ids": ["doc-1"],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["results"]) == 2

    def test_search_missing_query(self, test_client):
        """Test search without query field."""
        response = test_client.post(
            "/api/search",
            json={},
        )

        assert response.status_code == 422

    def test_search_empty_query(self, test_client):
        """Test search with empty query."""
        response = test_client.post(
            "/api/search",
            json={"query": ""},
        )

        assert response.status_code == 422

    def test_search_error_handling(self, test_client):
        """Test error handling in search."""
        with patch("storage.vector_store.EmbeddingGenerator") as mock_embedder:
            mock_instance = MagicMock()
            mock_instance.embed_text.side_effect = Exception("Embedding error")
            mock_embedder.return_value = mock_instance

            response = test_client.post(
                "/api/search",
                json={"query": "test"},
            )

            assert response.status_code == 500


class TestChatEndpoint:
    """Test cases for /api/chat endpoint."""

    def test_chat_success(self, test_client):
        """Test successful chat with valid data."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.return_value = {
                "answer": "Chat response",
                "sources": [
                    {"chunk_id": "chunk-1", "score": 0.95, "text": "Source"}
                ],
                "confidence": 0.95,
                "context_used": 1,
            }

            response = test_client.post(
                "/api/chat",
                json={
                    "message": "Hello",
                    "history": [],
                    "top_k": 5,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Chat response"
            assert len(data["sources"]) == 1
        finally:
            _clear_override(test_client)

    def test_chat_with_history(self, test_client):
        """Test chat with history."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.return_value = {
                "answer": "Follow-up response",
                "sources": [],
                "confidence": 0.9,
                "context_used": 1,
            }

            response = test_client.post(
                "/api/chat",
                json={
                    "message": "Follow-up question",
                    "history": [
                        {"role": "user", "content": "First message"},
                        {"role": "assistant", "content": "First response"},
                    ],
                },
            )

            assert response.status_code == 200
        finally:
            _clear_override(test_client)

    def test_chat_missing_message(self, test_client):
        """Test chat without message field."""
        response = test_client.post(
            "/api/chat",
            json={},
        )

        assert response.status_code == 422

    def test_chat_empty_message(self, test_client):
        """Test chat with empty message."""
        response = test_client.post(
            "/api/chat",
            json={"message": ""},
        )

        assert response.status_code == 422

    def test_chat_error_handling(self, test_client):
        """Test error handling in chat."""
        mock_pipeline = MagicMock()
        _override_rag_pipeline(test_client, mock_pipeline)
        try:
            mock_pipeline.query.side_effect = Exception("Pipeline error")

            response = test_client.post(
                "/api/chat",
                json={"message": "Test"},
            )

            assert response.status_code == 500
        finally:
            _clear_override(test_client)
