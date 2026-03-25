"""Neo4j graph database backend (optional)."""

from __future__ import annotations

from typing import Iterator

from philgraph.backends.base import GraphBackend
from philgraph.schema import Edge, EdgeProperties, EdgeType, NodeBase, NODE_TYPE_MAP


class Neo4jBackend(GraphBackend):
    """Graph backend using Neo4j database.

    Requires: pip install philgraph[neo4j]
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple[str, str] = ("neo4j", "password"),
        database: str = "neo4j",
    ) -> None:
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise ImportError(
                "Neo4jBackend requires the neo4j driver. "
                "Install with: pip install philgraph[neo4j]"
            )
        self._driver = GraphDatabase.driver(uri, auth=auth)
        self._database = database
        self._nodes: dict[str, NodeBase] = {}

    def close(self) -> None:
        self._driver.close()

    def add_node(self, node: NodeBase) -> None:
        node_type = type(node).__name__
        with self._driver.session(database=self._database) as session:
            session.run(
                f"MERGE (n:{node_type} {{uid: $uid}}) "
                f"SET n.label = $label",
                uid=node.uid, label=node.label,
            )
        self._nodes[node.uid] = node

    def get_node(self, uid: str) -> NodeBase | None:
        return self._nodes.get(uid)

    def remove_node(self, uid: str) -> None:
        with self._driver.session(database=self._database) as session:
            session.run("MATCH (n {uid: $uid}) DETACH DELETE n", uid=uid)
        self._nodes.pop(uid, None)

    def iter_nodes(self, node_type: str | None = None) -> Iterator[tuple[str, NodeBase]]:
        for uid, node in self._nodes.items():
            if node_type is None or type(node).__name__ == node_type:
                yield uid, node

    def add_edge(self, edge: Edge) -> None:
        rel_type = edge.edge_type.value.upper()
        with self._driver.session(database=self._database) as session:
            session.run(
                f"MATCH (a {{uid: $src}}), (b {{uid: $tgt}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                f"SET r.confidence = $conf",
                src=edge.source_uid, tgt=edge.target_uid,
                conf=edge.properties.confidence,
            )

    def get_edges(
        self, source_uid: str | None = None,
        target_uid: str | None = None,
        edge_type: EdgeType | None = None,
    ) -> list[Edge]:
        clauses = []
        params: dict = {}
        if source_uid:
            clauses.append("a.uid = $src")
            params["src"] = source_uid
        if target_uid:
            clauses.append("b.uid = $tgt")
            params["tgt"] = target_uid

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"MATCH (a)-[r]->(b) {where} RETURN a.uid, type(r), b.uid, r.confidence"

        results = []
        with self._driver.session(database=self._database) as session:
            for record in session.run(query, **params):
                try:
                    et = EdgeType(record[1].lower())
                except ValueError:
                    continue
                if edge_type and et != edge_type:
                    continue
                results.append(Edge(
                    source_uid=record[0], target_uid=record[2],
                    edge_type=et,
                    properties=EdgeProperties(confidence=record[3] or 1.0),
                ))
        return results

    def remove_edge(self, source_uid: str, target_uid: str, edge_type: EdgeType) -> None:
        rel_type = edge_type.value.upper()
        with self._driver.session(database=self._database) as session:
            session.run(
                f"MATCH (a {{uid: $src}})-[r:{rel_type}]->(b {{uid: $tgt}}) DELETE r",
                src=source_uid, tgt=target_uid,
            )

    def neighbors(
        self, uid: str, direction: str = "both",
        edge_types: list[EdgeType] | None = None,
    ) -> list[str]:
        nbrs: set[str] = set()
        if direction in ("out", "both"):
            query = "MATCH (a {uid: $uid})-[r]->(b) RETURN type(r), b.uid"
            with self._driver.session(database=self._database) as session:
                for record in session.run(query, uid=uid):
                    try:
                        et = EdgeType(record[0].lower())
                    except ValueError:
                        continue
                    if edge_types is None or et in edge_types:
                        nbrs.add(record[1])
        if direction in ("in", "both"):
            query = "MATCH (a)-[r]->(b {uid: $uid}) RETURN type(r), a.uid"
            with self._driver.session(database=self._database) as session:
                for record in session.run(query, uid=uid):
                    try:
                        et = EdgeType(record[0].lower())
                    except ValueError:
                        continue
                    if edge_types is None or et in edge_types:
                        nbrs.add(record[1])
        return list(nbrs)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        with self._driver.session(database=self._database) as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r)")
            return result.single()[0]

    def subgraph(self, uids: set[str]) -> Neo4jBackend:
        # For subgraph, fall back to in-memory filtering
        from philgraph.backends.networkx_backend import NetworkXBackend
        nx_backend = NetworkXBackend()
        for uid in uids:
            node = self._nodes.get(uid)
            if node:
                nx_backend.add_node(node)
        for edge in self.get_edges():
            if edge.source_uid in uids and edge.target_uid in uids:
                nx_backend.add_edge(edge)
        return nx_backend

    def clear(self) -> None:
        with self._driver.session(database=self._database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        self._nodes.clear()
