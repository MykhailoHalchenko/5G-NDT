"""Workflow orchestration for network activation (stub).

Manages the lifecycle of activation workflows:
  request → validate → execute → verify → notify
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class WorkflowStep:
    """A single step within an activation workflow."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.status: WorkflowStatus = WorkflowStatus.PENDING
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class ActivationWorkflow:
    """Represents a single network service activation workflow instance."""

    def __init__(
        self,
        workflow_type: str,
        target_entity_id: UUID,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id: UUID = uuid4()
        self.workflow_type = workflow_type
        self.target_entity_id = target_entity_id
        self.parameters = parameters or {}
        self.status: WorkflowStatus = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_type": self.workflow_type,
            "target_entity_id": str(self.target_entity_id),
            "parameters": self.parameters,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkflowEngine:
    """Orchestrates network activation workflows.

    The stub logs calls and returns empty / no-op responses.
    In Phase 5 this will drive real NETCONF/YANG or Ansible executions.
    """

    def __init__(self) -> None:
        self._workflows: Dict[UUID, ActivationWorkflow] = {}
        logger.info("WorkflowEngine initialised (stub)")

    def submit(self, workflow: ActivationWorkflow) -> UUID:
        """Submit a workflow for execution.

        Args:
            workflow: The workflow to execute.

        Returns:
            UUID of the submitted workflow.
        """
        self._workflows[workflow.id] = workflow
        logger.info(
            "WorkflowEngine.submit() — stub, id=%s type=%s",
            workflow.id,
            workflow.workflow_type,
        )
        return workflow.id

    def get_status(self, workflow_id: UUID) -> Optional[ActivationWorkflow]:
        """Return the current state of a workflow."""
        logger.debug("WorkflowEngine.get_status(id=%s) — stub", workflow_id)
        return self._workflows.get(workflow_id)

    def cancel(self, workflow_id: UUID) -> bool:
        """Cancel a pending or running workflow.

        Returns:
            True if cancelled successfully, False otherwise.
        """
        logger.info("WorkflowEngine.cancel(id=%s) — stub", workflow_id)
        return False

    def rollback(self, workflow_id: UUID) -> bool:
        """Roll back a completed or failed workflow.

        Returns:
            True if rollback succeeded, False otherwise.
        """
        logger.info("WorkflowEngine.rollback(id=%s) — stub", workflow_id)
        return False

    def list_workflows(self) -> List[ActivationWorkflow]:
        """Return all submitted workflows."""
        return list(self._workflows.values())
