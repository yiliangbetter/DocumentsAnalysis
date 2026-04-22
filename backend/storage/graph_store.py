"""Lightweight graph sidecar store for document/chunk/entity relations."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import settings
from core.document import DocumentChunk


class GraphStore:
    """Persist a small relation graph for hybrid retrieval experiments."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.GRAPH_STORE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, document_id: str) -> Path:
        return self.storage_path / f"{document_id}.json"

    def upsert_document_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> None:
        """Store graph nodes/edges derived from chunk entity metadata."""
        chunk_nodes = []
        entity_nodes = {}
        edges = []

        for chunk in chunks:
            chunk_node_id = f"chunk:{chunk.id}"
            chunk_nodes.append(
                {
                    "id": chunk_node_id,
                    "kind": "chunk",
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                }
            )
            edges.append(
                {
                    "source": f"document:{document_id}",
                    "target": chunk_node_id,
                    "type": "chunk_in_document",
                    "confidence": 1.0,
                }
            )

            entities = chunk.metadata.get("entities", [])
            confidence_map = chunk.metadata.get("entity_confidence", {})
            for entity in entities:
                entity_id = f"entity:{entity.lower()}"
                entity_nodes[entity_id] = {
                    "id": entity_id,
                    "kind": "entity",
                    "name": entity,
                }
                edges.append(
                    {
                        "source": chunk_node_id,
                        "target": entity_id,
                        "type": "mentions",
                        "confidence": float(confidence_map.get(entity, 0.5)),
                    }
                )

        graph = {
            "document_id": document_id,
            "nodes": [
                {"id": f"document:{document_id}", "kind": "document", "document_id": document_id},
                *chunk_nodes,
                *entity_nodes.values(),
            ],
            "edges": edges,
        }

        with open(self._get_file_path(document_id), "w", encoding="utf-8") as file:
            json.dump(graph, file, indent=2)

    def delete_by_document_id(self, document_id: str) -> bool:
        """Delete graph sidecar for a document."""
        path = self._get_file_path(document_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def get_stats(self) -> Dict[str, int]:
        """Get simple graph store stats."""
        files = list(self.storage_path.glob("*.json"))
        return {"documents_indexed": len(files)}

    def expand_related_chunks(
        self,
        seed_chunk_ids: List[str],
        limit: int = 10,
    ) -> List[Tuple[str, float]]:
        """Expand chunk candidates through shared entity mentions.

        Returns tuples of (chunk_id, relation_score) sorted descending.
        """
        if not seed_chunk_ids or limit <= 0:
            return []

        seed_nodes = {f"chunk:{chunk_id}" for chunk_id in seed_chunk_ids}
        entity_weights: Dict[str, float] = {}
        candidate_scores: Dict[str, float] = {}

        for graph_file in self.storage_path.glob("*.json"):
            try:
                with open(graph_file, "r", encoding="utf-8") as file:
                    graph = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            edges = graph.get("edges", [])
            # Stage 1: gather entities connected from seed chunks.
            for edge in edges:
                if edge.get("type") != "mentions":
                    continue
                source = edge.get("source")
                target = edge.get("target")
                if source in seed_nodes and target:
                    entity_weights[target] = max(
                        entity_weights.get(target, 0.0),
                        float(edge.get("confidence", 0.5)),
                    )

            # Stage 2: score other chunks that mention those entities.
            for edge in edges:
                if edge.get("type") != "mentions":
                    continue
                source = edge.get("source")
                target = edge.get("target")
                if not source or not target or source in seed_nodes:
                    continue
                if not source.startswith("chunk:"):
                    continue
                if target not in entity_weights:
                    continue
                score = entity_weights[target] * float(edge.get("confidence", 0.5))
                candidate_scores[source] = max(candidate_scores.get(source, 0.0), score)

        ranked = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        return [(chunk_node.split("chunk:", 1)[1], score) for chunk_node, score in ranked]
