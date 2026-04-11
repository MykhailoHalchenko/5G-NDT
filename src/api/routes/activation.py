"""Activation service — sync helpers and async FastAPI router.

Provides functions to submit and manage network activation workflows,
and exposes them as async HTTP endpoints via a FastAPI APIRouter.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
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


# ── Request / Response schemas ────────────────────────────────────────────────


class WorkflowSubmitRequest(BaseModel):
    """Request body for submitting an activation workflow."""

    workflow_type: str
    target_entity_id: UUID
    parameters: Optional[Dict[str, Any]] = None


# ── FastAPI async router ───────────────────────────────────────────────────────

router = APIRouter(prefix="/activation", tags=["Activation"])


@router.get(
    "/workflows",
    summary="List all activation workflows",
)
async def api_list_workflows() -> List[Dict[str, Any]]:
    """Return all submitted activation workflows and their current status."""
    return list_workflows()


@router.post(
    "/workflows",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new activation workflow",
)
async def api_submit_workflow(body: WorkflowSubmitRequest) -> Dict[str, Any]:
    """Validate and submit a network activation workflow.

    Returns the new workflow ID and initial status ``pending``.
    Raises HTTP 422 if pre-flight validation fails.
    """
    try:
        return submit_workflow(
            workflow_type=body.workflow_type,
            target_entity_id=body.target_entity_id,
            parameters=body.parameters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/workflows/{workflow_id}",
    summary="Get the status of an activation workflow",
)
async def api_get_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Return the current state of a specific activation workflow."""
    wf = get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


@router.delete(
    "/workflows/{workflow_id}/cancel",
    summary="Cancel a pending or running workflow",
)
async def api_cancel_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Cancel the specified workflow. Returns success flag."""
    cancelled = cancel_workflow(workflow_id)
    return {"workflow_id": str(workflow_id), "cancelled": cancelled}


@router.post(
    "/workflows/{workflow_id}/rollback",
    summary="Roll back a completed or failed workflow",
)
async def api_rollback_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Attempt to roll back the specified workflow. Returns success flag."""
    rolled_back = rollback_workflow(workflow_id)
    return {"workflow_id": str(workflow_id), "rolled_back": rolled_back}
