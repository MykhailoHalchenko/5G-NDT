"""Network activation REST endpoints.

POST /api/v1/activation/          — submit a new activation workflow
GET  /api/v1/activation/{id}      — get workflow status
POST /api/v1/activation/{id}/cancel  — cancel a workflow
POST /api/v1/activation/{id}/rollback — rollback a workflow
GET  /api/v1/activation/          — list all workflows
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...core.activation.validators import ActivationValidator
from ...core.activation.workflow import ActivationWorkflow, WorkflowEngine

router = APIRouter(prefix="/activation", tags=["activation"])

_engine = WorkflowEngine()
_validator = ActivationValidator()


class ActivationRequest(BaseModel):
    """Request body for submitting a new activation workflow."""

    workflow_type: str = Field(..., description="Type of workflow, e.g. 'slice_activation'")
    target_entity_id: UUID = Field(..., description="UUID of the target network entity")
    parameters: Dict[str, Any] = Field(default_factory=dict)


@router.get("/", response_model=List[Dict[str, Any]], summary="List all activation workflows")
async def list_workflows() -> List[Dict[str, Any]]:
    """Return all submitted activation workflows."""
    return [w.to_dict() for w in _engine.list_workflows()]


@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new activation workflow",
)
async def submit_workflow(request: ActivationRequest) -> Dict[str, Any]:
    """Validate and submit a network activation workflow for execution."""
    context = {
        "entity_id": str(request.target_entity_id),
        **request.parameters,
    }
    if not _validator.is_approved(context):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Activation request failed pre-flight validation",
        )
    workflow = ActivationWorkflow(
        workflow_type=request.workflow_type,
        target_entity_id=request.target_entity_id,
        parameters=request.parameters,
    )
    workflow_id = _engine.submit(workflow)
    return {"workflow_id": str(workflow_id), "status": "pending"}


@router.get(
    "/{workflow_id}",
    response_model=Dict[str, Any],
    summary="Get activation workflow status",
)
async def get_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Return the current state of an activation workflow."""
    workflow = _engine.get_status(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )
    return workflow.to_dict()


@router.post(
    "/{workflow_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel an activation workflow",
)
async def cancel_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Cancel a pending or running workflow."""
    success = _engine.cancel(workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow {workflow_id} could not be cancelled",
        )
    return {"workflow_id": str(workflow_id), "status": "cancelled"}


@router.post(
    "/{workflow_id}/rollback",
    response_model=Dict[str, Any],
    summary="Rollback an activation workflow",
)
async def rollback_workflow(workflow_id: UUID) -> Dict[str, Any]:
    """Roll back a completed or failed workflow."""
    success = _engine.rollback(workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow {workflow_id} could not be rolled back",
        )
    return {"workflow_id": str(workflow_id), "status": "rolled_back"}
