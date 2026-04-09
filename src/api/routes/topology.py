"""Topology query service (replaces FastAPI router).

Provides functions to query the in-memory topology store.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from ...core.topology.models import (
    Connection,
    NetworkSlice,
    TopologySnapshot,
    gNodeB,
)

# In-memory store (replaced by GraphDBConnector in Phase 2)
_gnodebs: dict[UUID, gNodeB] = {}
_slices: dict[UUID, NetworkSlice] = {}
_connections: dict[UUID, Connection] = {}


def get_topology() -> TopologySnapshot:
    """Return the current topology snapshot."""
    return TopologySnapshot(
        gnodebs=list(_gnodebs.values()),
        slices=list(_slices.values()),
        connections=list(_connections.values()),
    )


def list_gnodebs() -> List[gNodeB]:
    return list(_gnodebs.values())


def get_gnodeb(gnb_id: UUID) -> Optional[gNodeB]:
    return _gnodebs.get(gnb_id)


def list_slices() -> List[NetworkSlice]:
    return list(_slices.values())


def get_slice(slice_id: UUID) -> Optional[NetworkSlice]:
    return _slices.get(slice_id)


def list_connections() -> List[Connection]:
    return list(_connections.values())
