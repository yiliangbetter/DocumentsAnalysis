"""RAG (Retrieval-Augmented Generation) pipeline."""
import json
from typing import List, Optional

import openai

from config import settings
from core.document import DocumentChunk
from storage.vector_store import VectorStore


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for question answering."""

    def __init__(
        self,
        vector_store: VectorStore,
        openai_client: Optional[openai.OpenAI] = None,
    ):
        self.vector_store = vector_store
        self.client = openai_client or openai.OpenAI(
            api_key=settings.KIMI_API_KEY,
            base_url=settings.KIMI_BASE_URL
        )
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.top_k = settings.TOP_K_RETRIEVAL

    def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """
        Execute a RAG query: retrieve relevant chunks and generate answer.

        Args:
            question: The user's question
            document_ids: Optional list of document IDs to search within
            top_k: Number of chunks to retrieve (default from settings)

        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            # Step 1: Embed the question
            from storage.vector_store import EmbeddingGenerator

            embedder = EmbeddingGenerator()
            query_embedding = embedder.embed_text(question)

            # Step 2: Retrieve relevant chunks
            k = top_k or self.top_k
            retrieved = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=k,
                document_ids=document_ids,
            )

            # Step 3: Generate answer (with or without context)
            if not retrieved:
                # No relevant chunks found - ask LLM directly without context
                answer = self._generate_answer_direct(question)
                sources = []
                confidence = 0.0
            else:
                # Build context from retrieved chunks and generate answer
                context = self._build_context(retrieved)
                answer = self._generate_answer_with_context(question, context)
                sources = self._format_sources(retrieved)
                confidence = sum(score for _, score, _ in retrieved) / len(retrieved)

            # Step 5: Format sources
            sources = self._format_sources(retrieved)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": round(confidence, 4) if isinstance(confidence, float) else confidence,
                "context_used": len(retrieved) if retrieved else 0,
            }

        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
            }

    def _build_context(self, retrieved: List[tuple]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, (chunk_id, score, text) in enumerate(retrieved, 1):
            context_parts.append(f"[Source {i}]\n{text}\n")

        return "\n---\n".join(context_parts)

    def _generate_answer_with_context(self, question: str, context: str) -> str:
        """Generate answer using Kimi K2.5 with retrieved context."""
        messages = [
            {
                "role": "system",
                "content": "You are a technical support assistant. Answer the question based ONLY on the provided context. If the context doesn't contain enough information, say 'I don't have enough information to answer this.' Cite specific sources (e.g., 'According to Source 1...') when providing information."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content

    def _generate_answer_direct(self, question: str) -> str:
        """Generate answer using Kimi K2.5 without retrieved context."""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer the question to the best of your knowledge. Be concise and accurate."
            },
            {
                "role": "user",
                "content": question
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content

    def _format_sources(self, retrieved: List[tuple]) -> List[dict]:
        """Format retrieved chunks as sources."""
        sources = []
        for chunk_id, score, text in retrieved:
            sources.append({
                "chunk_id": chunk_id,
                "score": round(score, 4),
                "text": text[:500] + "..." if len(text) > 500 else text,
            })
        return sources
