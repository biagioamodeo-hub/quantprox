from hmac import compare_digest

from fastapi import Cookie, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.sessions import read_session_token

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_tenant(
    api_key: str | None = Security(api_key_header),
    session_token: str | None = Cookie(default=None, alias="quantprox_session"),
) -> str:
    if api_key is not None:
        for tenant_id, expected_key in settings.tenant_api_keys.items():
            if compare_digest(api_key, expected_key):
                return tenant_id
    if session_token is not None:
        session_tenant_id = read_session_token(session_token)
        if session_tenant_id is not None:
            return session_tenant_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid X-API-Key header is required.",
        headers={"WWW-Authenticate": "ApiKey"},
    )
