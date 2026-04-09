"""Topology REST endpoints.

GET /api/v1/topology          — full topology snapshot
GET /api/v1/topology/gnodebs  — list gNodeBs
GET /api/v1/topology/gnodebs/{id} — single gNodeB
GET /api/v1/topology/slices   — list network slices
GET /api/v1/topology/connections — list connections
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ...core.topology.models import (
    Connection,
    NetworkSlice,
    TopologySnapshot,
    gNodeB,
)

router = APIRouter(prefix="/topology", tags=["topology"])

# In-memory store (replaced by GraphDBConnector in Phase 2)
_gnodebs: dict[UUID, gNodeB] = {}
_slices: dict[UUID, NetworkSlice] = {}
_connections: dict[UUID, Connection] = {}


@router.get("/", response_model=TopologySnapshot, summary="Get full topology snapshot")
async def get_topology() -> TopologySnapshot:
    """Return the current topology snapshot including all entities and connections."""
    return TopologySnapshot(
        gnodebs=list(_gnodebs.values()),
        slices=list(_slices.values()),
        connections=list(_connections.values()),
    )


@router.get("/gnodebs", response_model=List[gNodeB], summary="List all gNodeBs")
async def list_gnodebs() -> List[gNodeB]:
    """Return all registered gNodeB base stations."""
    return list(_gnodebs.values())


@router.get("/gnodebs/{gnb_id}", response_model=gNodeB, summary="Get gNodeB by ID")
async def get_gnodeb(gnb_id: UUID) -> gNodeB:
    """Return a single gNodeB by its UUID."""
    if gnb_id not in _gnodebs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"gNodeB {gnb_id} not found",
        )
    return _gnodebs[gnb_id]


@router.get("/slices", response_model=List[NetworkSlice], summary="List all network slices")
async def list_slices() -> List[NetworkSlice]:
    """Return all registered network slices."""
    return list(_slices.values())


@router.get("/slices/{slice_id}", response_model=NetworkSlice, summary="Get network slice by ID")
async def get_slice(slice_id: UUID) -> NetworkSlice:
    """Return a single NetworkSlice by its UUID."""
    if slice_id not in _slices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NetworkSlice {slice_id} not found",
        )
    return _slices[slice_id]


@router.get("/connections", response_model=List[Connection], summary="List all connections")
async def list_connections() -> List[Connection]:
    """Return all logical connections in the topology."""
    return list(_connections.values())
