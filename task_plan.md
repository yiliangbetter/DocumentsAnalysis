# Task Plan: Vector RAG vs GraphRAG Evaluation

## Goal
Evaluate the current vector-database RAG approach against a graph-based RAG approach, then define a low-risk implementation path for this repository.

## Scope
- Analyze current architecture and retrieval flow.
- Compare Vector RAG and GraphRAG across quality, complexity, cost, and operability.
- Recommend a phased rollout plan with measurable acceptance criteria.

## Phases
| Phase | Description | Status |
|---|---|---|
| 1 | Inspect current backend RAG implementation and tests | complete |
| 2 | Record findings about current data model and retrieval limitations | complete |
| 3 | Compare Vector RAG vs GraphRAG for this project context | complete |
| 4 | Propose recommended architecture and migration path | complete |
| 5 | Share practical next steps and validation checklist | complete |
| 6 | Implement retrieval abstraction and mode flag | complete |
| 7 | Validate behavior with tests/lints and document status | complete |
| 8 | Add graph sidecar schema enrichment during ingestion | complete |

## Decisions
- Prefer **hybrid evolution** (vector-first + graph augmentation) over replacing vector retrieval immediately.
- Use existing API surface (`/query`, `/search`, `/chat`) and add configurable retrieval mode to minimize migration risk.
- Build graph construction as asynchronous ingestion enrichment so query path remains resilient if graph is unavailable.

## Implementation Plan
1. **Baseline first**
   - Keep current vector retrieval as control.
   - Add retrieval telemetry: retrieval latency, prompt tokens, answer quality labels.
2. **Schema extension**
   - Extend `DocumentChunk.metadata` for entity mentions and link confidence.
   - Persist graph edges in a sidecar graph store (or local graph file for POC).
3. **Hybrid retriever**
   - Add `HybridRetriever` abstraction behind `RAGPipeline`.
   - Merge candidates: vector top-k + graph-neighborhood candidates, then rerank.
4. **Feature flag rollout**
   - Config flag per request/environment (`vector`, `hybrid`, optional `graph_only` for testing).
   - Keep API contract unchanged to avoid frontend breakage.
5. **Evaluation gate**
   - Use fixed benchmark questions with multi-hop and single-hop sets.
   - Promote only if hybrid improves quality with acceptable p95 latency and cost.

## Validation Checklist
- Accuracy/faithfulness improves on relation-heavy questions.
- Source citations show clearer evidence chains.
- p95 latency increase remains within acceptable SLO.
- Ingestion time increase is acceptable for your update frequency.
- Fallback to vector-only works when graph enrichment fails.

## Verification Notes
- `ReadLints` returned no diagnostics on changed files.
- Test execution is currently blocked in this environment because `pytest` is not available on PATH.

## Risks / Open Questions
- Whether current chunk metadata already provides enough relational signal.
- Whether graph extraction quality will justify added complexity.
- Operational overhead of introducing a graph database.

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| None yet | - | - |
