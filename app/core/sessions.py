import base64
import hashlib
import hmac
import json
import time

from app.core.config import settings


def create_session_token(tenant_id: str) -> str:
    payload = json.dumps(
        {
            "tenant_id": tenant_id,
            "expires_at": int(time.time()) + settings.session_ttl_seconds,
        },
        separators=(",", ":"),
    ).encode()
    encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(
        settings.session_secret.encode(), encoded.encode(), hashlib.sha256
    ).hexdigest()
    return f"{encoded}.{signature}"


def read_session_token(token: str) -> str | None:
    try:
        encoded, supplied_signature = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            settings.session_secret.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        padding = "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(encoded + padding))
        if int(payload["expires_at"]) <= int(time.time()):
            return None
        tenant_id = str(payload["tenant_id"])
        return tenant_id
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
