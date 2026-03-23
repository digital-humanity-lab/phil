"""High-level query API for PhilGraph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from philgraph.graph import PhilGraph

from philgraph.schema import EdgeType


class QueryAPI:
    """Convenience query interface wrapping PhilGraph methods."""

    def __init__(self, graph: PhilGraph):
        self.graph = graph

    def find_path(
        self,
        source_uid: str,
        target_uid: str,
        max_depth: int = 6,
        edge_types: list[str] | None = None,
    ) -> list[list[str]]:
        """Find paths between two nodes."""
        et = [EdgeType(e) for e in edge_types] if edge_types else None
        return self.graph.find_path(source_uid, target_uid, max_depth, et)

    def influence_network(
        self, thinker_uid: str, depth: int = 2, direction: str = "both"
    ) -> dict:
        """Get influence network as summary dict."""
        sub = self.graph.influence_network(thinker_uid, depth, direction)
        return sub.summary()

    def concept_cluster(
        self, concept_uid: str, depth: int = 2,
    ) -> dict:
        """Get concept cluster with communities and centrality."""
        return self.graph.concept_cluster(concept_uid, depth)

    def tradition_overlap(self, trad_a_uid: str, trad_b_uid: str) -> dict:
        """Compare two traditions."""
        return self.graph.tradition_overlap(trad_a_uid, trad_b_uid)

    def temporal_evolution(
        self, concept_uid: str, start_year: int, end_year: int,
        bin_size: int = 50,
    ) -> list[dict]:
        """Track concept evolution over time."""
        return self.graph.temporal_evolution(concept_uid, start_year, end_year, bin_size)

    def summary(self) -> dict:
        """Graph statistics."""
        return self.graph.summary()

    def export_graphml(self, path: str | Path) -> None:
        """Export graph to GraphML format."""
        import networkx as nx
        from philgraph.backend.networkx_backend import NetworkXBackend

        g = nx.MultiDiGraph()
        for uid, node in self.graph.iter_nodes():
            attrs = {"label": node.label, "type": type(node).__name__}
            for lang, lbl in node.labels_i18n.items():
                attrs[f"label_{lang}"] = lbl
            if hasattr(node, "birth_year") and node.birth_year:
                attrs["birth_year"] = node.birth_year
            if hasattr(node, "death_year") and node.death_year:
                attrs["death_year"] = node.death_year
            if hasattr(node, "definition") and node.definition:
                attrs["definition"] = node.definition
            g.add_node(uid, **attrs)
        for edge in self.graph.iter_edges():
            g.add_edge(
                edge.source_uid, edge.target_uid,
                key=edge.edge_type.value,
                confidence=edge.properties.confidence,
            )
        nx.write_graphml(g, str(path))

    def export_jsonld(self, path: str | Path) -> None:
        """Export graph to JSON-LD format."""
        context = {
            "@context": {
                "phil": "http://philgraph.org/ontology/",
                "phild": "http://philgraph.org/data/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "label": "rdfs:label",
            }
        }
        nodes = []
        for uid, node in self.graph.iter_nodes():
            nodes.append({
                "@id": f"phild:{uid}",
                "@type": f"phil:{type(node).__name__}",
                "label": node.label,
            })
        doc = {**context, "@graph": nodes}
        with open(path, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

    def export_cypher(self, path: str | Path) -> None:
        """Export graph as Cypher CREATE statements."""
        lines = []
        for uid, node in self.graph.iter_nodes():
            ntype = type(node).__name__
            label_esc = node.label.replace('"', '\\"')
            lines.append(
                f'CREATE (:{ntype} {{uid: "{uid}", label: "{label_esc}"}})'
            )
        for edge in self.graph.iter_edges():
            rel = edge.edge_type.value.upper()
            lines.append(
                f'MATCH (a {{uid: "{edge.source_uid}"}}), '
                f'(b {{uid: "{edge.target_uid}"}}) '
                f'CREATE (a)-[:{rel} {{confidence: {edge.properties.confidence}}}]->(b)'
            )
        with open(path, "w") as f:
            f.write(";\n".join(lines) + ";\n")

    def export_rdf(self, path: str | Path, format: str = "turtle") -> None:
        """Export graph to RDF."""
        from philgraph.backend.rdflib_backend import RDFLibBackend
        if isinstance(self.graph.backend, RDFLibBackend):
            self.graph.backend.export_rdf(str(path), format=format)
        else:
            rdf = RDFLibBackend()
            for uid, node in self.graph.iter_nodes():
                rdf.add_node(node)
            for edge in self.graph.iter_edges():
                rdf.add_edge(edge)
            rdf.export_rdf(str(path), format=format)
