from hmac import compare_digest

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_tenant(api_key: str | None = Security(api_key_header)) -> str:
    if api_key is not None:
        for tenant_id, expected_key in settings.tenant_api_keys.items():
            if compare_digest(api_key, expected_key):
                return tenant_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid X-API-Key header is required.",
        headers={"WWW-Authenticate": "ApiKey"},
    )
