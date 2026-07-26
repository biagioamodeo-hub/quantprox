import hashlib
import json

from pydantic import BaseModel


def request_fingerprint(payload: BaseModel | None) -> str:
    data = payload.model_dump(mode="json", exclude_none=True) if payload else {}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
