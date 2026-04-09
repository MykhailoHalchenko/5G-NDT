"""Unit tests for 5G topology data models."""

from __future__ import annotations

import pytest
from uuid import uuid4

from src.core.topology.models import (
    CU,
    DU,
    Connection,
    ConnectionType,
    FrequencyBand,
    KPI,
    KPISeverity,
    NetworkSlice,
    NodeStatus,
    SliceQoSProfile,
    SliceType,
    TopologySnapshot,
    gNodeB,
)


# ── gNodeB ────────────────────────────────────────────────────────────────────


class TestGNodeB:
    def test_create_minimal(self):
        gnb = gNodeB(name="gNB-1", gnb_id=1, plmn_id="26601")
        assert gnb.gnb_id == 1
        assert gnb.plmn_id == "26601"
        assert gnb.status == NodeStatus.INACTIVE
        assert gnb.cu_ids == []
        assert gnb.du_ids == []

    def test_create_full(self):
        cu_id = uuid4()
        du_id = uuid4()
        gnb = gNodeB(
            name="gNB-Full",
            gnb_id=42,
            plmn_id="26601",
            frequency_bands=[FrequencyBand.N78, FrequencyBand.N41],
            status=NodeStatus.ACTIVE,
            ip_address="192.168.1.1",
            vendor="Ericsson",
            software_version="v21.Q4",
            cu_ids=[cu_id],
            du_ids=[du_id],
        )
        assert gnb.status == NodeStatus.ACTIVE
        assert len(gnb.frequency_bands) == 2
        assert gnb.vendor == "Ericsson"
        assert cu_id in gnb.cu_ids

    def test_id_auto_generated(self):
        gnb1 = gNodeB(name="gNB-A", gnb_id=1, plmn_id="26601")
        gnb2 = gNodeB(name="gNB-B", gnb_id=2, plmn_id="26601")
        assert gnb1.id != gnb2.id

    def test_name_required(self):
        with pytest.raises(Exception):
            gNodeB(gnb_id=1, plmn_id="26601")

    def test_name_empty_string_rejected(self):
        with pytest.raises(Exception):
            gNodeB(name="", gnb_id=1, plmn_id="26601")


# ── CU ────────────────────────────────────────────────────────────────────────


class TestCU:
    def test_create_minimal(self):
        cu = CU(name="CU-1")
        assert cu.name == "CU-1"
        assert cu.status == NodeStatus.INACTIVE
        assert cu.connected_dus == []

    def test_port_validation(self):
        cu = CU(name="CU-2", port=38472)
        assert cu.port == 38472

    def test_port_out_of_range(self):
        with pytest.raises(Exception):
            CU(name="CU-Bad", port=99999)


# ── DU ────────────────────────────────────────────────────────────────────────


class TestDU:
    def test_create_minimal(self):
        du = DU(name="DU-1", cell_id=100)
        assert du.cell_id == 100
        assert du.frequency_band == FrequencyBand.N78

    def test_load_bounds(self):
        du = DU(name="DU-2", cell_id=1, current_load_percent=50.0)
        assert du.current_load_percent == 50.0

    def test_load_over_100_rejected(self):
        with pytest.raises(Exception):
            DU(name="DU-Bad", cell_id=1, current_load_percent=101.0)

    def test_load_negative_rejected(self):
        with pytest.raises(Exception):
            DU(name="DU-Bad2", cell_id=1, current_load_percent=-1.0)


# ── NetworkSlice ──────────────────────────────────────────────────────────────


class TestNetworkSlice:
    def _qos(self, **kwargs) -> SliceQoSProfile:
        defaults = dict(
            max_downlink_mbps=1000.0,
            max_uplink_mbps=500.0,
            max_latency_ms=5.0,
        )
        defaults.update(kwargs)
        return SliceQoSProfile(**defaults)

    def test_create_embb(self):
        sl = NetworkSlice(
            name="eMBB-Slice-1",
            s_nssai="1:000001",
            slice_type=SliceType.EMBB,
            qos_profile=self._qos(),
        )
        assert sl.slice_type == SliceType.EMBB
        assert sl.status == NodeStatus.INACTIVE

    def test_create_urllc(self):
        sl = NetworkSlice(
            name="URLLC-Slice",
            s_nssai="2:000002",
            slice_type=SliceType.URLLC,
            qos_profile=self._qos(max_latency_ms=1.0),
        )
        assert sl.slice_type == SliceType.URLLC

    def test_qos_zero_bandwidth_rejected(self):
        with pytest.raises(Exception):
            SliceQoSProfile(max_downlink_mbps=0, max_uplink_mbps=100, max_latency_ms=5)

    def test_qos_priority_bounds(self):
        qos = self._qos()
        assert 1 <= qos.priority <= 10


# ── KPI ───────────────────────────────────────────────────────────────────────


class TestKPI:
    def test_create(self):
        kpi = KPI(
            entity_id=uuid4(),
            entity_type="gNodeB",
            metric_name="latency_ms",
            value=4.5,
            unit="ms",
        )
        assert kpi.value == 4.5
        assert kpi.unit == "ms"

    def test_compute_severity_info(self):
        kpi = KPI(
            entity_id=uuid4(),
            entity_type="gNodeB",
            metric_name="latency_ms",
            value=5.0,
            warning_threshold=10.0,
            critical_threshold=50.0,
        )
        assert kpi.compute_severity() == KPISeverity.INFO

    def test_compute_severity_warning(self):
        kpi = KPI(
            entity_id=uuid4(),
            entity_type="gNodeB",
            metric_name="latency_ms",
            value=15.0,
            warning_threshold=10.0,
            critical_threshold=50.0,
        )
        assert kpi.compute_severity() == KPISeverity.WARNING

    def test_compute_severity_critical(self):
        kpi = KPI(
            entity_id=uuid4(),
            entity_type="gNodeB",
            metric_name="latency_ms",
            value=55.0,
            warning_threshold=10.0,
            critical_threshold=50.0,
        )
        assert kpi.compute_severity() == KPISeverity.CRITICAL

    def test_severity_no_thresholds(self):
        kpi = KPI(
            entity_id=uuid4(),
            entity_type="gNodeB",
            metric_name="some_metric",
            value=999.0,
        )
        assert kpi.compute_severity() == KPISeverity.INFO


# ── Connection ────────────────────────────────────────────────────────────────


class TestConnection:
    def test_create(self):
        conn = Connection(
            source_id=uuid4(),
            target_id=uuid4(),
            connection_type=ConnectionType.F1,
        )
        assert conn.is_active is True
        assert conn.connection_type == ConnectionType.F1

    def test_all_connection_types(self):
        for ct in ConnectionType:
            conn = Connection(source_id=uuid4(), target_id=uuid4(), connection_type=ct)
            assert conn.connection_type == ct


# ── TopologySnapshot ──────────────────────────────────────────────────────────


class TestTopologySnapshot:
    def test_empty_snapshot(self):
        snap = TopologySnapshot()
        assert snap.gnodebs == []
        assert snap.cus == []
        assert snap.dus == []
        assert snap.slices == []
        assert snap.connections == []

    def test_snapshot_with_entities(self):
        gnb = gNodeB(name="gNB-1", gnb_id=1, plmn_id="26601")
        snap = TopologySnapshot(gnodebs=[gnb])
        assert len(snap.gnodebs) == 1
        assert snap.gnodebs[0].name == "gNB-1"
