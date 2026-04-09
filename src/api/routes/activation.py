"""Activation service (replaces FastAPI router).

Provides functions to submit and manage network activation workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from ...core.activation.validators import ActivationValidator
from ...core.activation.workflow import ActivationWorkflow, WorkflowEngine

_engine = WorkflowEngine()
_validator = ActivationValidator()


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
