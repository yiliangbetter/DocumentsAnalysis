# Findings: Vector RAG vs GraphRAG

## Context
- User concern: vector storage may miss intrinsic relations among chunks.
- Target: evaluate whether GraphRAG should replace or complement current retrieval.

## Repository Findings
- `RAGPipeline` is purely vector-search based: query embedding -> `vector_store.search(...)` -> prompt with top-k chunk text.
- Current retrieval context is a flat list of chunks (`[Source i]`), with no explicit entity or relation traversal.
- Fallback behavior exists: if no chunk is retrieved, pipeline calls the LLM directly without retrieval context.
- `config.py` exposes vector-oriented controls (`TOP_K_RETRIEVAL`, chunk size/overlap, similarity threshold) and no graph-retrieval toggles.
- Existing tests focus on LLM communication shape and live integration; there are no tests for multi-hop retrieval or cross-chunk relation reasoning.
- `VectorStore` persists only lightweight metadata (`document_id`, `chunk_index`, `start_char`, `end_char`) and does not store typed relations between chunks/entities.
- `DocumentChunk` has a generic `metadata` field but it is not currently used by `VectorStore.add_chunks(...)`, so relation-aware retrieval is not implemented.

## External/Conceptual Findings
- **Vector RAG strengths**: simple architecture, low operational overhead, strong for lexical/semantic nearest-neighbor retrieval, and easy to evaluate/iterate.
- **Vector RAG weakness**: weak explicit multi-hop reasoning (entity A -> relation -> entity B), especially when evidence is spread across distant chunks.
- **GraphRAG strengths**: explicit entity/relation structure supports path-based retrieval, better provenance chains, and improved queries requiring relationship reasoning.
- **GraphRAG weaknesses**: graph construction quality is brittle (entity extraction + relation linking), ingestion latency rises, and operational complexity increases (graph storage + indexing + maintenance).
- **Practical pattern in production**: hybrid retrieval usually works best (vector recall first, graph expansion/rerank second) instead of full replacement.

## Candidate Recommendations
- Start with **Hybrid RAG**, not immediate full GraphRAG replacement.
- Keep Chroma as primary semantic retrieval to preserve current behavior and latency baseline.
- Add a lightweight knowledge-graph sidecar from chunk content:
  - Nodes: document, chunk, entity.
  - Edges: `chunk_in_document`, `mentions`, optional `co_occurs` (same chunk/window), optional extracted typed relations.
- Retrieval strategy:
  1. Vector retrieve top-k chunks.
  2. Extract/resolve salient entities from query.
  3. Expand 1-2 graph hops from top chunks/entities.
  4. Rerank merged candidates, then build context.
- Gate rollout behind feature flags and A/B evaluation:
  - `RETRIEVAL_MODE=vector|hybrid|graph`
  - Track exact-match/F1 (or task success), source quality, latency p95, and token cost.

## Implementation Progress
- Added `RETRIEVAL_MODE` to backend settings with default `vector`.
- Added retriever abstraction in `backend/core/retrievers.py`:
  - `VectorRetriever` (existing behavior),
  - `HybridRetriever` scaffold (currently vector-equivalent for safe rollout),
  - `build_retriever(...)` factory.
- Wired `RAGPipeline` to call `self.retriever.retrieve(...)` instead of hardcoding `vector_store.search(...)`.
- Added tests for mode selection (`vector`, `hybrid`) in `backend/tests/core/test_rag.py`.
- Step 2 implementation added:
  - Chunk-level metadata enrichment in `DocumentProcessor` (`entities`, `entity_confidence`).
  - New `GraphStore` sidecar (`backend/storage/graph_store.py`) for document/chunk/entity nodes and relation edges.
  - Upload/delete flow now syncs graph sidecar in `backend/api/documents.py`.
  - Backend startup/health now initializes and reports graph store stats.
- Step 3 implementation added:
  - `HybridRetriever` now performs vector recall + graph expansion + merged reranking.
  - `GraphStore` can expand related chunk candidates via shared entity mentions.
  - `VectorStore` can fetch chunk texts by chunk ID for graph-expanded candidates.
  - Query pipeline now passes graph store into `RAGPipeline` for hybrid mode.
