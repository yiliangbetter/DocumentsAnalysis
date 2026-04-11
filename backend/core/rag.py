"""RAG (Retrieval-Augmented Generation) pipeline."""
import json
from typing import List, Optional

from anthropic import Anthropic

from config import settings
from core.document import DocumentChunk
from storage.vector_store import VectorStore


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for question answering."""

    def __init__(
        self,
        vector_store: VectorStore,
        anthropic_client: Optional[Anthropic] = None,
    ):
        self.vector_store = vector_store
        self.client = anthropic_client or Anthropic(api_key=settings.ANTHROPIC_API_KEY)
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

            if not retrieved:
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "sources": [],
                    "confidence": 0.0,
                }

            # Step 3: Build context from retrieved chunks
            context = self._build_context(retrieved)

            # Step 4: Generate answer using Claude
            answer = self._generate_answer(question, context)

            # Step 5: Format sources
            sources = self._format_sources(retrieved)

            # Calculate confidence (average of similarity scores)
            confidence = sum(score for _, score, _ in retrieved) / len(retrieved)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": round(confidence, 4),
                "context_used": len(retrieved),
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

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Claude."""
        prompt = f"""You are a technical support assistant. Answer the question based ONLY on the provided context.
If the context doesn't contain enough information, say "I don't have enough information to answer this."
Cite specific sources (e.g., "According to Source 1...") when providing information.

Context:
{context}

Question: {question}

Answer:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

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
