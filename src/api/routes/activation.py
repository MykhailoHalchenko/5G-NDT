"""Activation service — sync helpers and async aiohttp route handlers.

Provides functions to submit and manage network activation workflows,
and exposes them as async HTTP endpoints via aiohttp RouteTableDef.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import pydantic
from aiohttp import web
from pydantic import BaseModel

from ...core.activation.validators import ActivationValidator
from ...core.activation.workflow import ActivationWorkflow, WorkflowEngine

_engine = WorkflowEngine()
_validator = ActivationValidator()

# ── Sync helpers (used directly in integration tests) ─────────────────────────


def list_workflows() -> List[Dict[str, Any]]:
    return [w.to_dict() for w in _engine.list_workflows()]


def submit_workflow(
    workflow_type: str,
    target_entity_id: UUID,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate and submit an activation workflow.

    Returns:
        Dict with 'workflow_id' and 'status', or raises ValueError on validation failure.
    """
    params = parameters or {}
    context = {"entity_id": str(target_entity_id), **params}
    if not _validator.is_approved(context):
        raise ValueError("Activation request failed pre-flight validation")
    workflow = ActivationWorkflow(
        workflow_type=workflow_type,
        target_entity_id=target_entity_id,
        parameters=params,
    )
    workflow_id = _engine.submit(workflow)
    return {"workflow_id": str(workflow_id), "status": "pending"}


def get_workflow(workflow_id: UUID) -> Optional[Dict[str, Any]]:
    workflow = _engine.get_status(workflow_id)
    return workflow.to_dict() if workflow else None


def cancel_workflow(workflow_id: UUID) -> bool:
    return _engine.cancel(workflow_id)


def rollback_workflow(workflow_id: UUID) -> bool:
    return _engine.rollback(workflow_id)


# ── Request schema ────────────────────────────────────────────────────────────


class WorkflowSubmitRequest(BaseModel):
    """Request body schema for submitting an activation workflow."""

    workflow_type: str
    target_entity_id: UUID
    parameters: Optional[Dict[str, Any]] = None


# ── aiohttp async route handlers ──────────────────────────────────────────────

routes = web.RouteTableDef()


@routes.get("/api/v1/activation/workflows")
async def api_list_workflows(request: web.Request) -> web.Response:
    """Return all submitted activation workflows and their current status."""
    return web.json_response(list_workflows())


@routes.post("/api/v1/activation/workflows")
async def api_submit_workflow(request: web.Request) -> web.Response:
    """Validate and submit a network activation workflow.

    Returns HTTP 202 with the new workflow ID and initial status ``pending``.
    Returns HTTP 400 on malformed JSON, HTTP 422 on validation failure.
    """
    try:
        body_data = await request.json()
    except Exception:
        raise web.HTTPBadRequest(reason="Request body must be valid JSON")
    try:
        body = WorkflowSubmitRequest(**body_data)
    except pydantic.ValidationError as exc:
        raise web.HTTPUnprocessableEntity(
            text=json.dumps({"detail": exc.errors()}),
            content_type="application/json",
        )
    try:
        result = submit_workflow(
            workflow_type=body.workflow_type,
            target_entity_id=body.target_entity_id,
            parameters=body.parameters,
        )
    except ValueError as exc:
        raise web.HTTPUnprocessableEntity(
            text=json.dumps({"detail": str(exc)}),
            content_type="application/json",
        )
    return web.json_response(result, status=202)


@routes.get("/api/v1/activation/workflows/{workflow_id}")
async def api_get_workflow(request: web.Request) -> web.Response:
    """Return the current state of a specific activation workflow."""
    try:
        workflow_id = UUID(request.match_info["workflow_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    wf = get_workflow(workflow_id)
    if wf is None:
        raise web.HTTPNotFound(reason="Workflow not found")
    return web.json_response(wf)


@routes.delete("/api/v1/activation/workflows/{workflow_id}/cancel")
async def api_cancel_workflow(request: web.Request) -> web.Response:
    """Cancel the specified workflow. Returns a success flag."""
    try:
        workflow_id = UUID(request.match_info["workflow_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    cancelled = cancel_workflow(workflow_id)
    return web.json_response({"workflow_id": str(workflow_id), "cancelled": cancelled})


@routes.post("/api/v1/activation/workflows/{workflow_id}/rollback")
async def api_rollback_workflow(request: web.Request) -> web.Response:
    """Attempt to roll back the specified workflow. Returns a success flag."""
    try:
        workflow_id = UUID(request.match_info["workflow_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    rolled_back = rollback_workflow(workflow_id)
    return web.json_response({"workflow_id": str(workflow_id), "rolled_back": rolled_back})


def register_routes(app: web.Application) -> None:
    """Register all activation route handlers with an aiohttp Application."""
    app.add_routes(routes)
