"""Tests for philgraph schema, backends, and ingestion.

All tests run WITHOUT requiring Neo4j, rdflib, or any external service.
"""

import pytest

from philgraph.schema import (
    Concept, Thinker, Text, Tradition, Argument, Era, Institution, Language,
    Edge, EdgeType, EdgeProperties, ConsensusLevel, NodeBase, NODE_TYPE_MAP,
    EDGE_CONSTRAINTS,
)
from philgraph.backends.networkx_backend import NetworkXBackend
from philgraph.graph import PhilGraph


# ── Schema node types ───────────────────────────────────────────────

def test_schema_node_types():
    """All 8 node types exist in NODE_TYPE_MAP."""
    expected = {"Concept", "Thinker", "Text", "Tradition",
                "Argument", "Era", "Institution", "Language"}
    assert expected == set(NODE_TYPE_MAP.keys())


def test_schema_node_creation():
    """Create instances of each node type."""
    c = Concept(uid="c1", label="仁", definition="Confucian humaneness")
    assert c.uid == "c1"
    assert c.definition == "Confucian humaneness"

    t = Thinker(uid="t1", label="Confucius", birth_year=-551, death_year=-479)
    assert t.birth_year == -551

    txt = Text(uid="txt1", label="Analects", year=-400, language="zh")
    assert txt.language == "zh"


# ── Schema edge types ──────────────────────────────────────────────

def test_schema_edge_types():
    """All edge types exist."""
    expected_edges = {
        "influences", "opposes", "extends", "reinterprets",
        "translates_to", "analogous_to", "subsumes",
        "uses_in_argument", "authored_by", "belongs_to_tradition",
        "contemporary_with", "affiliated_with", "written_in",
        "part_of_era", "cites",
    }
    actual = {e.value for e in EdgeType}
    assert expected_edges == actual


def test_edge_constraints_exist():
    """EDGE_CONSTRAINTS has entries for all edge types."""
    for et in EdgeType:
        assert et in EDGE_CONSTRAINTS, f"Missing constraint for {et}"


# ── NetworkXBackend ─────────────────────────────────────────────────

def test_networkx_backend_add_node():
    """Add and retrieve a node."""
    backend = NetworkXBackend()
    node = Concept(uid="c1", label="Dao", definition="The Way")
    backend.add_node(node)

    retrieved = backend.get_node("c1")
    assert retrieved is not None
    assert retrieved.label == "Dao"
    assert isinstance(retrieved, Concept)
    assert backend.node_count() == 1


def test_networkx_backend_add_edge():
    """Add edge between two nodes."""
    backend = NetworkXBackend()
    c1 = Concept(uid="c1", label="Ren")
    c2 = Concept(uid="c2", label="Li")
    backend.add_node(c1)
    backend.add_node(c2)

    edge = Edge(
        source_uid="c1", target_uid="c2",
        edge_type=EdgeType.EXTENDS,
        properties=EdgeProperties(confidence=0.9),
    )
    backend.add_edge(edge)
    assert backend.edge_count() == 1


def test_networkx_backend_get_edges():
    """Retrieve edges with filters."""
    backend = NetworkXBackend()
    c1 = Concept(uid="c1", label="A")
    c2 = Concept(uid="c2", label="B")
    c3 = Concept(uid="c3", label="C")
    backend.add_node(c1)
    backend.add_node(c2)
    backend.add_node(c3)

    backend.add_edge(Edge(source_uid="c1", target_uid="c2",
                          edge_type=EdgeType.EXTENDS))
    backend.add_edge(Edge(source_uid="c1", target_uid="c3",
                          edge_type=EdgeType.OPPOSES))

    edges_from_c1 = backend.get_edges(source_uid="c1")
    assert len(edges_from_c1) == 2

    extends_only = backend.get_edges(edge_type=EdgeType.EXTENDS)
    assert len(extends_only) == 1


def test_networkx_backend_iter_nodes():
    """Iterate nodes, optionally by type."""
    backend = NetworkXBackend()
    backend.add_node(Concept(uid="c1", label="A"))
    backend.add_node(Thinker(uid="t1", label="B"))
    backend.add_node(Concept(uid="c2", label="C"))

    all_nodes = list(backend.iter_nodes())
    assert len(all_nodes) == 3

    concepts = list(backend.iter_nodes("Concept"))
    assert len(concepts) == 2


def test_networkx_backend_iter_edges():
    """Iterate all edges."""
    backend = NetworkXBackend()
    backend.add_node(Concept(uid="c1", label="A"))
    backend.add_node(Concept(uid="c2", label="B"))
    backend.add_edge(Edge(source_uid="c1", target_uid="c2",
                          edge_type=EdgeType.ANALOGOUS_TO))
    edges = backend.get_edges()
    assert len(edges) == 1
    assert edges[0].edge_type == EdgeType.ANALOGOUS_TO


def test_networkx_backend_neighbors():
    """Find neighbors with direction filter."""
    backend = NetworkXBackend()
    backend.add_node(Concept(uid="c1", label="A"))
    backend.add_node(Concept(uid="c2", label="B"))
    backend.add_node(Concept(uid="c3", label="C"))
    backend.add_edge(Edge(source_uid="c1", target_uid="c2",
                          edge_type=EdgeType.EXTENDS))
    backend.add_edge(Edge(source_uid="c3", target_uid="c1",
                          edge_type=EdgeType.OPPOSES))

    out_nbrs = backend.neighbors("c1", direction="out")
    assert "c2" in out_nbrs

    in_nbrs = backend.neighbors("c1", direction="in")
    assert "c3" in in_nbrs

    both_nbrs = backend.neighbors("c1", direction="both")
    assert len(both_nbrs) == 2


def test_networkx_backend_subgraph():
    """Create subgraph from node set."""
    backend = NetworkXBackend()
    for i in range(4):
        backend.add_node(Concept(uid=f"c{i}", label=f"N{i}"))
    backend.add_edge(Edge(source_uid="c0", target_uid="c1",
                          edge_type=EdgeType.EXTENDS))
    backend.add_edge(Edge(source_uid="c2", target_uid="c3",
                          edge_type=EdgeType.OPPOSES))

    sub = backend.subgraph({"c0", "c1"})
    assert sub.node_count() == 2
    assert sub.edge_count() == 1


# ── PhilGraph integration ──────────────────────────────────────────

def test_philgraph_edge_constraint():
    """Invalid edge type-pair raises ValueError."""
    g = PhilGraph()
    g.add_node(Concept(uid="c1", label="A"))
    g.add_node(Text(uid="txt1", label="B"))
    with pytest.raises(ValueError, match="Invalid edge"):
        # EXTENDS only allows Concept->Concept or Argument->Argument
        g.add_edge(Edge(source_uid="c1", target_uid="txt1",
                        edge_type=EdgeType.EXTENDS))


def test_philgraph_summary():
    """Summary returns node/edge counts."""
    g = PhilGraph()
    g.add_node(Concept(uid="c1", label="A"))
    g.add_node(Thinker(uid="t1", label="B"))
    s = g.summary()
    assert s["total_nodes"] == 2
    assert s["nodes_by_type"]["Concept"] == 1
    assert s["nodes_by_type"]["Thinker"] == 1


# ── ManualIngester ──────────────────────────────────────────────────

def test_manual_ingester():
    """Load from YAML dict (simulated)."""
    from philgraph.ingest.manual import ManualIngester

    g = PhilGraph()
    ingester = ManualIngester(g)
    data = {
        "nodes": [
            {"type": "Concept", "uid": "c_ren", "label": "仁",
             "definition": "Humaneness"},
            {"type": "Concept", "uid": "c_li", "label": "礼",
             "definition": "Ritual propriety"},
            {"type": "Thinker", "uid": "t_confucius", "label": "Confucius",
             "birth_year": -551, "death_year": -479},
        ],
        "edges": [
            {"source": "c_ren", "target": "c_li",
             "type": "extends",
             "properties": {"confidence": 0.9}},
        ],
    }
    ingester._process_yaml(data)

    assert g.get_node("c_ren") is not None
    assert g.get_node("c_ren").label == "仁"
    assert g.get_node("t_confucius").birth_year == -551
    assert len(g.iter_edges()) == 1
    assert ingester.stats["nodes_added"] == 3
    assert ingester.stats["edges_added"] == 1
