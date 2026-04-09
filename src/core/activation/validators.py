"""Safety validators for network activation requests (stub).

Each validator checks a specific pre-condition before a workflow is
allowed to proceed, preventing unsafe or conflicting changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    passed: bool
    validator_name: str
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class BaseValidator:
    """Abstract base class for activation validators."""

    name: str = "base_validator"

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Run the validation against the provided context.

        Args:
            context: Arbitrary dict with request parameters and entity state.

        Returns:
            ValidationResult indicating pass/fail.
        """
        raise NotImplementedError


class EntityExistsValidator(BaseValidator):
    """Validates that the target entity exists in the topology."""

    name = "entity_exists"

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        entity_id = context.get("entity_id")
        logger.debug("EntityExistsValidator.validate(entity_id=%s) — stub", entity_id)
        # TODO: query GraphDBConnector to verify entity existence
        return ValidationResult(
            passed=True,
            validator_name=self.name,
            message=f"Entity {entity_id} existence check (stub — always passes)",
        )


class SliceCapacityValidator(BaseValidator):
    """Validates that the target slice has sufficient available capacity."""

    name = "slice_capacity"

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        slice_id = context.get("slice_id")
        requested_bw = context.get("requested_bandwidth_mbps", 0)
        logger.debug(
            "SliceCapacityValidator.validate(slice_id=%s, bw=%s) — stub",
            slice_id,
            requested_bw,
        )
        return ValidationResult(
            passed=True,
            validator_name=self.name,
            message="Slice capacity check (stub — always passes)",
        )


class MaintenanceWindowValidator(BaseValidator):
    """Validates that no maintenance window is currently active for the target."""

    name = "maintenance_window"

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        entity_id = context.get("entity_id")
        logger.debug("MaintenanceWindowValidator.validate(entity_id=%s) — stub", entity_id)
        return ValidationResult(
            passed=True,
            validator_name=self.name,
            message="Maintenance window check (stub — always passes)",
        )


class ActivationValidator:
    """Composite validator that runs all registered validators in sequence.

    All validators must pass for the activation to be approved.
    """

    DEFAULT_VALIDATORS: List[BaseValidator] = [
        EntityExistsValidator(),
        SliceCapacityValidator(),
        MaintenanceWindowValidator(),
    ]

    def __init__(self, validators: Optional[List[BaseValidator]] = None) -> None:
        self._validators = validators if validators is not None else list(self.DEFAULT_VALIDATORS)
        logger.info(
            "ActivationValidator initialised with %d validators",
            len(self._validators),
        )

    def add_validator(self, validator: BaseValidator) -> None:
        """Register an additional validator."""
        self._validators.append(validator)

    def validate_all(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """Run all validators and return their results.

        Args:
            context: Activation request context dict.

        Returns:
            List of ValidationResult, one per validator.
        """
        results = []
        for validator in self._validators:
            result = validator.validate(context)
            results.append(result)
            if not result.passed:
                logger.warning(
                    "Validation failed: validator=%s message=%s",
                    result.validator_name,
                    result.message,
                )
        return results

    def is_approved(self, context: Dict[str, Any]) -> bool:
        """Return True only if all validators pass."""
        return all(r.passed for r in self.validate_all(context))
