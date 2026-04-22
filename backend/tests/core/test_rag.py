"""Tests for the RAG pipeline's Kimi communication path."""
import os
from unittest.mock import MagicMock

import pytest

from core.rag import RAGPipeline
from core.retrievers import GraphRetriever, HybridRetriever, VectorRetriever


class TestRAGPipelineKimiCommunication:
    """Verify RAG pipeline communicates with Kimi successfully."""

    def test_generate_answer_direct_calls_kimi_client_successfully(self):
        """It should call Kimi chat completions and return content."""
        mock_vector_store = MagicMock()
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Kimi direct answer"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        pipeline = RAGPipeline(vector_store=mock_vector_store, openai_client=mock_client)

        result = pipeline._generate_answer_direct("What is DocumentsAnalysis?")

        assert result == "Kimi direct answer"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == pipeline.model
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["content"] == "What is DocumentsAnalysis?"

    def test_generate_answer_with_context_calls_kimi_client_successfully(self):
        """It should send context to Kimi and return content."""
        mock_vector_store = MagicMock()
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Kimi context answer"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        pipeline = RAGPipeline(vector_store=mock_vector_store, openai_client=mock_client)
        context = "[Source 1]\nKimi is available.\n"

        result = pipeline._generate_answer_with_context("Is Kimi online?", context)

        assert result == "Kimi context answer"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == pipeline.model
        assert "Context:\n[Source 1]" in call_kwargs["messages"][1]["content"]
        assert "Question: Is Kimi online?" in call_kwargs["messages"][1]["content"]


class TestRAGPipelineKimiLiveIntegration:
    """Optional live integration tests against real Kimi API."""

    @pytest.mark.integration
    def test_generate_answer_direct_live_kimi_api(self, monkeypatch):
        """Call Kimi endpoint directly when env vars are provided."""
        kimi_api_key = os.getenv("KIMI_API_KEY")
        if not kimi_api_key:
            pytest.skip("KIMI_API_KEY not set; skipping live Kimi integration test.")

        kimi_base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
        llm_model = os.getenv("LLM_MODEL", "kimi-k2.5")

        from core import rag as rag_module

        monkeypatch.setattr(rag_module.settings, "KIMI_API_KEY", kimi_api_key)
        monkeypatch.setattr(rag_module.settings, "KIMI_BASE_URL", kimi_base_url)
        monkeypatch.setattr(rag_module.settings, "LLM_MODEL", llm_model)
        monkeypatch.setattr(rag_module.settings, "MAX_TOKENS", 64)
        monkeypatch.setattr(rag_module.settings, "TEMPERATURE", 0.0)

        pipeline = RAGPipeline(vector_store=MagicMock())
        answer = pipeline._generate_answer_direct("Reply with exactly: OK")

        assert isinstance(answer, str)
        assert answer.strip() == "OK"


class TestRAGPipelineRetrievalModes:
    """Verify retriever selection from settings."""

    def test_uses_vector_retriever_by_default(self, monkeypatch):
        from core import rag as rag_module

        monkeypatch.setattr(rag_module.settings, "RETRIEVAL_MODE", "vector")
        pipeline = RAGPipeline(vector_store=MagicMock(), openai_client=MagicMock())
        assert isinstance(pipeline.retriever, VectorRetriever)

    def test_uses_hybrid_retriever_when_configured(self, monkeypatch):
        from core import rag as rag_module

        monkeypatch.setattr(rag_module.settings, "RETRIEVAL_MODE", "hybrid")
        pipeline = RAGPipeline(
            vector_store=MagicMock(),
            graph_store=MagicMock(),
            openai_client=MagicMock(),
        )
        assert isinstance(pipeline.retriever, HybridRetriever)

    def test_uses_graph_retriever_when_configured(self, monkeypatch):
        from core import rag as rag_module

        monkeypatch.setattr(rag_module.settings, "RETRIEVAL_MODE", "graph")
        pipeline = RAGPipeline(
            vector_store=MagicMock(),
            graph_store=MagicMock(),
            openai_client=MagicMock(),
        )
        assert isinstance(pipeline.retriever, GraphRetriever)
