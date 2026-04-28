"""Graph store backed by Neo4j with a file-based fallback."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import settings
from core.document import DocumentChunk

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - handled in runtime paths
    GraphDatabase = None


class GraphStore:
    """Persist document/chunk/entity relations for retrieval expansion."""

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        driver: Optional[Any] = None,
    ):
        self.storage_path = storage_path or settings.GRAPH_STORE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.neo4j_uri = uri if uri is not None else settings.NEO4J_URI
        self.neo4j_user = user if user is not None else settings.NEO4J_USER
        self.neo4j_password = password if password is not None else settings.NEO4J_PASSWORD
        self.neo4j_database = database if database is not None else settings.NEO4J_DATABASE
        self._driver = driver

        self._use_neo4j = bool(self.neo4j_uri or self._driver)
        if self._use_neo4j and self._driver is None:
            if GraphDatabase is None:
                raise RuntimeError("neo4j package is required when NEO4J_URI is set")
            auth = (
                (self.neo4j_user, self.neo4j_password)
                if self.neo4j_user and self.neo4j_password
                else None
            )
            self._driver = GraphDatabase.driver(self.neo4j_uri, auth=auth)

    def _get_file_path(self, document_id: str) -> Path:
        return self.storage_path / f"{document_id}.json"

    def _run(self, query: str, **params: Any):
        with self._driver.session(database=self.neo4j_database) as session:
            return session.run(query, **params)

    def upsert_document_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> None:
        """Store graph nodes/edges derived from chunk entity metadata."""
        if self._use_neo4j:
            chunk_payload: List[Dict[str, Any]] = []
            for chunk in chunks:
                entities = chunk.metadata.get("entities", [])
                confidence_map = chunk.metadata.get("entity_confidence", {})
                chunk_payload.append(
                    {
                        "id": chunk.id,
                        "chunk_index": chunk.chunk_index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "entities": entities,
                        "entity_confidence": confidence_map,
                    }
                )

            self._run(
                """
                MERGE (d:Document {id: $document_id})
                WITH d
                UNWIND $chunks AS chunk
                MERGE (c:Chunk {id: chunk.id})
                SET c.chunk_index = chunk.chunk_index,
                    c.start_char = chunk.start_char,
                    c.end_char = chunk.end_char,
                    c.document_id = $document_id
                MERGE (d)-[:HAS_CHUNK]->(c)
                WITH c, chunk
                UNWIND chunk.entities AS entity_name
                MERGE (e:Entity {id: toLower(entity_name)})
                SET e.name = entity_name
                MERGE (c)-[m:MENTIONS]->(e)
                SET m.confidence = toFloat(coalesce(chunk.entity_confidence[entity_name], 0.5))
                """,
                document_id=document_id,
                chunks=chunk_payload,
            )
            return

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
                entity_nodes[entity_id] = {"id": entity_id, "kind": "entity", "name": entity}
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
        """Delete graph data for a document."""
        if self._use_neo4j:
            summary = self._run(
                """
                MATCH (d:Document {id: $document_id})
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                DETACH DELETE d, c
                """,
                document_id=document_id,
            ).consume()
            self._run(
                """
                MATCH (e:Entity)
                WHERE NOT (():Chunk)-[:MENTIONS]->(e)
                DETACH DELETE e
                """
            )
            return (summary.counters.nodes_deleted or 0) > 0

        path = self._get_file_path(document_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def get_stats(self) -> Dict[str, int]:
        """Get graph store stats."""
        if self._use_neo4j:
            result = self._run("MATCH (d:Document) RETURN count(d) AS documents_indexed").single()
            return {"documents_indexed": int(result["documents_indexed"]) if result else 0}

        files = list(self.storage_path.glob("*.json"))
        return {"documents_indexed": len(files)}

    def expand_related_chunks(
        self,
        seed_chunk_ids: List[str],
        limit: int = 10,
    ) -> List[Tuple[str, float]]:
        """Expand chunk candidates through shared entity mentions."""
        if not seed_chunk_ids or limit <= 0:
            return []

        if self._use_neo4j:
            records = self._run(
                """
                MATCH (seed:Chunk)-[seedMention:MENTIONS]->(entity:Entity)<-[candidateMention:MENTIONS]-(candidate:Chunk)
                WHERE seed.id IN $seed_chunk_ids AND NOT candidate.id IN $seed_chunk_ids
                WITH candidate.id AS chunk_id,
                     max(toFloat(seedMention.confidence) * toFloat(candidateMention.confidence)) AS relation_score
                RETURN chunk_id, relation_score
                ORDER BY relation_score DESC
                LIMIT $limit
                """,
                seed_chunk_ids=seed_chunk_ids,
                limit=limit,
            )
            return [(record["chunk_id"], float(record["relation_score"])) for record in records]

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
