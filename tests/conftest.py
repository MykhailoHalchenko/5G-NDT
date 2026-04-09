"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from src.core.topology.models import (
    DU,
    CU,
    FrequencyBand,
    NetworkSlice,
    NodeStatus,
    SliceQoSProfile,
    SliceType,
    TopologySnapshot,
    gNodeB,
)


@pytest.fixture
def sample_gnodeb() -> gNodeB:
    return gNodeB(
        name="gNB-Test-01",
        gnb_id=1,
        plmn_id="26601",
        frequency_bands=[FrequencyBand.N78],
        status=NodeStatus.ACTIVE,
    )


@pytest.fixture
def sample_du() -> DU:
    return DU(name="DU-Test-01", cell_id=100, tx_power_dbm=23.0, status=NodeStatus.ACTIVE)


@pytest.fixture
def sample_snapshot(sample_gnodeb, sample_du) -> TopologySnapshot:
    return TopologySnapshot(gnodebs=[sample_gnodeb], dus=[sample_du])
