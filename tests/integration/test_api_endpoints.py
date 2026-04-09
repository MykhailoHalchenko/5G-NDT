"""Integration tests for the pytwinnet-based Digital Twin and service modules."""

from __future__ import annotations

import pytest
from uuid import uuid4

from pytwinnet import DigitalTwin, Network, WirelessNode

from src.api.main import build_digital_twin, get_twin_snapshot, _build_sample_snapshot
from src.api.routes.topology import get_topology, list_gnodebs, list_slices, list_connections
from src.api.routes.metrics import get_metric_definitions, get_metrics_for_entity_type, get_kpi_summary
from src.api.routes.activation import list_workflows, submit_workflow, get_workflow
from src.core.topology.models import TopologySnapshot


class TestDigitalTwinBuilder:
    def test_build_from_empty_snapshot(self):
        twin = build_digital_twin(TopologySnapshot())
        assert isinstance(twin, DigitalTwin)
        assert twin.network.list_nodes() == []

    def test_build_from_sample_snapshot(self):
        snapshot = _build_sample_snapshot()
        twin = build_digital_twin(snapshot)
        nodes = twin.network.list_nodes()
        assert len(nodes) >= 1  # at least the gNodeB

    def test_snapshot_returns_dict(self):
        twin = build_digital_twin(TopologySnapshot())
        snap = get_twin_snapshot(twin)
        assert isinstance(snap, dict)

    def test_gnodeb_node_added(self, sample_gnodeb, sample_du):
        from src.core.topology.models import TopologySnapshot
        snapshot = TopologySnapshot(gnodebs=[sample_gnodeb], dus=[sample_du])
        twin = build_digital_twin(snapshot)
        node_ids = [n.node_id for n in twin.network.list_nodes()]
        assert str(sample_gnodeb.id) in node_ids
        assert str(sample_du.id) in node_ids


class TestTopologyService:
    def test_get_topology_returns_snapshot(self):
        snap = get_topology()
        assert hasattr(snap, "gnodebs")
        assert hasattr(snap, "slices")
        assert hasattr(snap, "connections")

    def test_list_gnodebs_returns_list(self):
        assert isinstance(list_gnodebs(), list)

    def test_list_slices_returns_list(self):
        assert isinstance(list_slices(), list)

    def test_list_connections_returns_list(self):
        assert isinstance(list_connections(), list)


class TestMetricsService:
    def test_get_metric_definitions_non_empty(self):
        defs = get_metric_definitions()
        assert len(defs) > 0

    def test_metric_definition_has_required_fields(self):
        first = get_metric_definitions()[0]
        assert "name" in first
        assert "unit" in first
        assert "description" in first

    def test_metrics_for_gnodeb(self):
        metrics = get_metrics_for_entity_type("gNodeB")
        names = [m["name"] for m in metrics]
        assert "latency_ms" in names

    def test_kpi_summary_returns_dict(self):
        result = get_kpi_summary(uuid4())
        assert "entity_id" in result
        assert "kpis" in result


class TestActivationService:
    def test_list_workflows_initially_empty(self):
        # may have entries from other tests; just check type
        assert isinstance(list_workflows(), list)

    def test_submit_and_retrieve_workflow(self):
        result = submit_workflow(
            workflow_type="slice_activation",
            target_entity_id=uuid4(),
            parameters={"slice_type": "eMBB"},
        )
        assert result["status"] == "pending"
        wf_id = result["workflow_id"]

        retrieved = get_workflow(uuid4().__class__(wf_id))
        assert retrieved is not None
        assert retrieved["id"] == wf_id

    def test_get_nonexistent_workflow_returns_none(self):
        assert get_workflow(uuid4()) is None
