"""Authentication and RBAC helpers — FastAPI security dependency + standalone stub."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency: extract and validate the Bearer token.

    Raises HTTP 401 if no valid credentials are provided.
    """
    token = credentials.credentials if credentials else ""
    user = authenticate(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
