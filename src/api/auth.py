"""Authentication and RBAC stub.

In production, replace the stub token decoder with a real JWT verification
against your IdP (e.g. Keycloak, Auth0).
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
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


def _decode_token(token: str) -> Optional[AuthenticatedUser]:
    """Decode and validate a bearer token (stub).

    TODO: Replace with real JWT verification (e.g. python-jose).
    """
    logger.debug("_decode_token() — stub, token length=%d", len(token))
    # Stub: accept any non-empty token and grant viewer access
    if token:
        return AuthenticatedUser(user_id="stub-user", username="stub", role=Role.VIEWER)
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency that extracts and validates the bearer token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _decode_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: Role):
    """Factory for a FastAPI dependency that enforces a minimum role level."""

    async def _check(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role.value}",
            )
        return user

    return _check
