"""Authentication and RBAC stub (no longer depends on FastAPI)."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class AuthenticatedUser:
    """Represents the currently authenticated principal."""

    def __init__(self, user_id: str, username: str, role: Role) -> None:
        self.user_id = user_id
        self.username = username
        self.role = role

    def has_role(self, required_role: Role) -> bool:
        role_order = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}
        return role_order[self.role] >= role_order[required_role]


def authenticate(token: str) -> Optional[AuthenticatedUser]:
    """Validate a token and return the authenticated user, or None.

    TODO: Replace with real JWT verification (e.g. python-jose).
    """
    logger.debug("authenticate() — stub, token length=%d", len(token))
    if token:
        return AuthenticatedUser(user_id="stub-user", username="stub", role=Role.VIEWER)
    return None
