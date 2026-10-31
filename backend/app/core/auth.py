"""Verify the short-lived JWTs issued by the auth service.

Known limit: a banned user's token stays valid until it expires (at most 15 minutes).
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import get_settings
from app.models.enums import Role

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    role: Role


@lru_cache
def get_jwks_client() -> PyJWKClient:
    # Keys are cached. An unknown kid (a new key after rotation) makes the client refetch, but at
    # most once a minute, so tokens with made-up kids can't flood the auth service.
    return PyJWKClient(
        get_settings().auth_jwks_url, cache_keys=True, timeout=3, cooldown_duration=60
    )


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    jwks_client: Annotated[PyJWKClient, Depends(get_jwks_client)],
) -> CurrentUser:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    settings = get_settings()
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["EdDSA"],
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
            options={"require": ["exp", "iat", "sub", "role"]},
        )
    except jwt.PyJWKClientConnectionError as error:
        logger.exception("could not fetch the JWKS")
        raise HTTPException(status_code=503, detail="Auth service unavailable") from error
    except (jwt.PyJWKClientError, jwt.InvalidTokenError) as error:
        raise _unauthorized("Invalid token") from error

    subject = claims["sub"]
    if not isinstance(subject, str):
        raise _unauthorized("Invalid token")
    try:
        role = Role(claims["role"])
    except ValueError as error:
        raise _unauthorized("Invalid token") from error
    return CurrentUser(id=subject, role=role)


def require_role(*roles: Role) -> Callable[[CurrentUser], CurrentUser]:
    def dependency(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return dependency
