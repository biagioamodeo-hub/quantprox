from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    id: int
    kind: str
    status: Literal["queued", "running", "succeeded", "failed"]
    attempts: int
    max_attempts: int
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
