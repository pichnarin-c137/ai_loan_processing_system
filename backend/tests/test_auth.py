import time
from collections.abc import Iterator
from typing import Annotated, Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from jwt import PyJWKClient

from app.core.auth import CurrentUser, get_jwks_client, require_role
from app.core.config import get_settings
from app.main import app
from app.models.enums import Role

KID = "test-key"
KEY = Ed25519PrivateKey.generate()
OTHER_KEY = Ed25519PrivateKey.generate()
JWKS = {"keys": [{**jwt.algorithms.OKPAlgorithm.to_jwk(KEY.public_key(), as_dict=True),
                  "kid": KID, "alg": "EdDSA", "use": "sig"}]}  # fmt: skip


class FakeJWKClient(PyJWKClient):
    def __init__(self, error: Exception | None = None) -> None:
        super().__init__("http://jwks.invalid")
        self.error = error

    def fetch_data(self) -> Any:
        if self.error:
            raise self.error
        return JWKS


@pytest.fixture(autouse=True)
def fake_jwks() -> Iterator[None]:
    app.dependency_overrides[get_jwks_client] = lambda: FakeJWKClient()
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def claims(**overrides: Any) -> dict[str, Any]:
    settings = get_settings()
    now = int(time.time())
    base: dict[str, Any] = {
        "iss": settings.auth_issuer,
        "aud": settings.auth_audience,
        "sub": "user-1",
        "iat": now,
        "exp": now + 900,
        "role": "analyst",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def token(
    payload: dict[str, Any] | None = None, key: Ed25519PrivateKey = KEY, kid: str = KID
) -> str:
    return jwt.encode(
        claims() if payload is None else payload, key, algorithm="EdDSA", headers={"kid": kid}
    )


def get_me(auth: str | None) -> Any:
    headers = {} if auth is None else {"Authorization": auth}
    return client.get("/api/me", headers=headers)


def test_valid_token() -> None:
    response = get_me(f"Bearer {token()}")

    assert response.status_code == 200
    assert response.json() == {"id": "user-1", "role": "analyst"}


def none_token() -> str:
    return jwt.encode(claims(), "", algorithm="none", headers={"kid": KID})


def hs256_token() -> str:
    public = KEY.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    secret = public.hex() * 2
    return jwt.encode(claims(), secret, algorithm="HS256", headers={"kid": KID})


BAD_AUTHS = {
    "no header": None,
    "basic scheme": "Basic xyz",
    "malformed": "Bearer not-a-jwt",
    "expired": f"Bearer {token(claims(iat=1, exp=2))}",
    "wrong key": f"Bearer {token(key=OTHER_KEY)}",
    "wrong iss": f"Bearer {token(claims(iss='http://evil.example'))}",
    "wrong aud": f"Bearer {token(claims(aud='other-api'))}",
    "missing role": f"Bearer {token(claims(role=None))}",
    "missing sub": f"Bearer {token(claims(sub=None))}",
    "non-string sub": f"Bearer {token(claims(sub=42))}",
    "unknown role": f"Bearer {token(claims(role='superuser'))}",
    "unknown kid": f"Bearer {token(kid='nope')}",
    "alg none": f"Bearer {none_token()}",
    "alg HS256": f"Bearer {hs256_token()}",
}


@pytest.mark.parametrize("auth", BAD_AUTHS.values(), ids=BAD_AUTHS.keys())
def test_rejected_token(auth: str | None) -> None:
    response = get_me(auth)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["detail"] in {"Not authenticated", "Invalid token"}


def test_jwks_unavailable() -> None:
    error = jwt.PyJWKClientConnectionError("secret-host refused")
    app.dependency_overrides[get_jwks_client] = lambda: FakeJWKClient(error)

    response = get_me(f"Bearer {token()}")

    assert response.status_code == 503
    assert response.json() == {"detail": "Auth service unavailable"}
    assert "secret-host" not in response.text


def test_unknown_kid_refetch_is_throttled(monkeypatch: pytest.MonkeyPatch) -> None:
    jwks_client = get_jwks_client.__wrapped__()
    fetches = 0

    def fetch_data() -> Any:
        nonlocal fetches
        fetches += 1
        return JWKS

    monkeypatch.setattr(jwks_client, "fetch_data", fetch_data)
    app.dependency_overrides[get_jwks_client] = lambda: jwks_client

    for kid in ("made-up-1", "made-up-2", "made-up-3"):
        assert get_me(f"Bearer {token(kid=kid)}").status_code == 401
    assert get_me(f"Bearer {token()}").status_code == 200

    # One fetch to fill the cache and one refresh for the first unknown kid; the rest wait.
    assert fetches == 2


def test_require_role() -> None:
    router = APIRouter()

    @router.get("/managers")
    def managers(
        user: Annotated[CurrentUser, Depends(require_role(Role.MANAGER))],
    ) -> dict[str, str]:
        return {"id": user.id}

    role_app = FastAPI()
    role_app.include_router(router)
    role_app.dependency_overrides[get_jwks_client] = lambda: FakeJWKClient()
    role_client = TestClient(role_app)

    analyst = role_client.get("/managers", headers={"Authorization": f"Bearer {token()}"})
    manager_token = token(claims(role="manager"))
    manager = role_client.get("/managers", headers={"Authorization": f"Bearer {manager_token}"})

    assert analyst.status_code == 403
    assert manager.status_code == 200
    assert manager.json() == {"id": "user-1"}
