"""Topology query service — sync helper functions and async FastAPI router.

Provides functions to query the in-memory topology store and exposes them
as async HTTP endpoints via a FastAPI APIRouter.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

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

# ── Sync helpers (used directly in integration tests) ─────────────────────────


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


# ── FastAPI async router ───────────────────────────────────────────────────────

router = APIRouter(prefix="/topology", tags=["Topology"])


@router.get(
    "/",
    summary="Get full topology snapshot",
    response_model=None,
)
async def api_get_topology() -> Dict[str, Any]:
    """Return the current 5G network topology snapshot."""
    snap = get_topology()
    return snap.model_dump()


@router.get(
    "/gnodebs",
    summary="List all gNodeBs",
)
async def api_list_gnodebs() -> List[Dict[str, Any]]:
    """Return all registered gNodeB network elements."""
    return [g.model_dump() for g in list_gnodebs()]


@router.get(
    "/gnodebs/{gnb_id}",
    summary="Get a specific gNodeB by UUID",
)
async def api_get_gnodeb(gnb_id: UUID) -> Dict[str, Any]:
    """Return a single gNodeB, or 404 if not found."""
    gnb = get_gnodeb(gnb_id)
    if gnb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="gNodeB not found")
    return gnb.model_dump()


@router.get(
    "/slices",
    summary="List all network slices",
)
async def api_list_slices() -> List[Dict[str, Any]]:
    """Return all registered network slices."""
    return [s.model_dump() for s in list_slices()]


@router.get(
    "/slices/{slice_id}",
    summary="Get a specific network slice by UUID",
)
async def api_get_slice(slice_id: UUID) -> Dict[str, Any]:
    """Return a single network slice, or 404 if not found."""
    sl = get_slice(slice_id)
    if sl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network slice not found")
    return sl.model_dump()


@router.get(
    "/connections",
    summary="List all logical connections",
)
async def api_list_connections() -> List[Dict[str, Any]]:
    """Return all logical connections in the topology."""
    return [c.model_dump() for c in list_connections()]
