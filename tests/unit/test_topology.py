"""Unit tests for topology helpers (graph_db, discovery)."""

from __future__ import annotations

import pytest
from uuid import uuid4

from src.core.topology.graph_db import GraphDBConfig, GraphDBConnector
from src.core.topology.discovery import DiscoveryConfig, DiscoveryEngine
from src.core.topology.models import TopologySnapshot


class TestGraphDBConnector:
    def setup_method(self):
        self.config = GraphDBConfig(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
        )
        self.db = GraphDBConnector(self.config)

    def test_health_check_returns_false_stub(self):
        # Stub always returns False (no real connection)
        assert self.db.health_check() is False

    def test_list_nodes_returns_empty_stub(self):
        assert self.db.list_nodes("gNodeB") == []

    def test_get_node_returns_none_stub(self):
        assert self.db.get_node("gNodeB", uuid4()) is None

    def test_delete_node_returns_false_stub(self):
        assert self.db.delete_node("gNodeB", uuid4()) is False

    def test_upsert_node_returns_none_stub(self):
        result = self.db.upsert_node("gNodeB", {"id": str(uuid4()), "name": "test"})
        assert result is None

    def test_upsert_relationship_returns_false_stub(self):
        result = self.db.upsert_relationship(uuid4(), uuid4(), "CONNECTED_TO")
        assert result is False

    def test_get_neighbours_returns_empty_stub(self):
        assert self.db.get_neighbours(uuid4()) == []

    def test_run_query_returns_empty_stub(self):
        result = self.db.run_query("MATCH (n) RETURN n LIMIT 1")
        assert result == []


class TestDiscoveryEngine:
    def setup_method(self):
        config = DiscoveryConfig(poll_interval_seconds=30)
        graph_db = GraphDBConnector(GraphDBConfig())
        self.engine = DiscoveryEngine(config=config, graph_db=graph_db)

    def test_discover_all_returns_empty_snapshot(self):
        snapshot = self.engine.discover_all()
        assert isinstance(snapshot, TopologySnapshot)
        assert snapshot.gnodebs == []
        assert snapshot.slices == []

    def test_discover_node_returns_false_stub(self):
        assert self.engine.discover_node(uuid4()) is False

    def test_start_stop_no_exception(self):
        # Stub methods should not raise
        self.engine.start()
        self.engine.stop()
