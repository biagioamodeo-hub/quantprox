from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
from time import monotonic


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._windows: dict[str, tuple[float, int]] = {}

    def check(self, identity: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = monotonic()
        with self._lock:
            started_at, count = self._windows.get(identity, (now, 0))
            elapsed = now - started_at
            if elapsed >= window_seconds:
                started_at, count, elapsed = now, 0, 0.0
            if count >= limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after=max(1, int(window_seconds - elapsed + 0.999)),
                )
            count += 1
            self._windows[identity] = (started_at, count)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=max(0, limit - count),
                retry_after=0,
            )

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()


def rate_limit_identity(api_key: str | None, client_host: str | None) -> str:
    raw = api_key or client_host or "unknown"
    return sha256(raw.encode()).hexdigest()


rate_limiter = FixedWindowRateLimiter()
