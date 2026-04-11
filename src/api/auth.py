"""Authentication and RBAC helpers — pure Python + aiohttp request extractor."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from aiohttp.web import Request

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


async def extract_token(request: "Request") -> str:
    """Extract a Bearer token from the Authorization header of an aiohttp request.

    Returns:
        The raw token string, or an empty string if not present.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return ""


async def get_current_user(request: "Request") -> Optional[AuthenticatedUser]:
    """Extract and validate the Bearer token from an aiohttp request.

    Returns:
        An AuthenticatedUser on success, or None if authentication failed.
    """
    token = await extract_token(request)
    return authenticate(token)
