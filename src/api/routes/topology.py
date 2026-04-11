"""Topology query service — sync helper functions and async aiohttp route handlers.

Provides functions to query the in-memory topology store and exposes them
as async HTTP endpoints via aiohttp RouteTableDef.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from aiohttp import web

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


# ── aiohttp async route handlers ──────────────────────────────────────────────

routes = web.RouteTableDef()


@routes.get("/api/v1/topology/")
async def api_get_topology(request: web.Request) -> web.Response:
    """Return the current 5G network topology snapshot."""
    snap = get_topology()
    return web.json_response(snap.model_dump(mode="json"))


@routes.get("/api/v1/topology/gnodebs")
async def api_list_gnodebs(request: web.Request) -> web.Response:
    """Return all registered gNodeB network elements."""
    return web.json_response([g.model_dump(mode="json") for g in list_gnodebs()])


@routes.get("/api/v1/topology/gnodebs/{gnb_id}")
async def api_get_gnodeb(request: web.Request) -> web.Response:
    """Return a single gNodeB, or 404 if not found."""
    try:
        gnb_id = UUID(request.match_info["gnb_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    gnb = get_gnodeb(gnb_id)
    if gnb is None:
        raise web.HTTPNotFound(reason="gNodeB not found")
    return web.json_response(gnb.model_dump(mode="json"))


@routes.get("/api/v1/topology/slices")
async def api_list_slices(request: web.Request) -> web.Response:
    """Return all registered network slices."""
    return web.json_response([s.model_dump(mode="json") for s in list_slices()])


@routes.get("/api/v1/topology/slices/{slice_id}")
async def api_get_slice(request: web.Request) -> web.Response:
    """Return a single network slice, or 404 if not found."""
    try:
        slice_id = UUID(request.match_info["slice_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    sl = get_slice(slice_id)
    if sl is None:
        raise web.HTTPNotFound(reason="Network slice not found")
    return web.json_response(sl.model_dump(mode="json"))


@routes.get("/api/v1/topology/connections")
async def api_list_connections(request: web.Request) -> web.Response:
    """Return all logical connections in the topology."""
    return web.json_response([c.model_dump(mode="json") for c in list_connections()])


def register_routes(app: web.Application) -> None:
    """Register all topology route handlers with an aiohttp Application."""
    app.add_routes(routes)
