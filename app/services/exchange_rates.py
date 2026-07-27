import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Lock
from urllib.request import Request, urlopen

from app.schemas.market_data import ExchangeRateRead

_cache: dict[tuple[str, str], tuple[datetime, ExchangeRateRead]] = {}
_cache_lock = Lock()
_cache_ttl = timedelta(minutes=15)


def get_exchange_rate(base: str, quote: str) -> ExchangeRateRead:
    pair = (base.upper(), quote.upper())
    now = datetime.now(UTC)
    with _cache_lock:
        cached = _cache.get(pair)
        if cached is not None and now - cached[0] < _cache_ttl:
            return cached[1]

    request = Request(
        f"https://api.frankfurter.dev/v2/rate/{pair[0]}/{pair[1]}",
        headers={"User-Agent": "QuantProX/1.0"},
    )
    with urlopen(request, timeout=5) as response:  # noqa: S310
        payload = json.load(response)
    result = ExchangeRateRead(
        base=payload["base"],
        quote=payload["quote"],
        rate=Decimal(str(payload["rate"])),
        rate_date=payload["date"],
        fetched_at=now,
        source="Frankfurter",
    )
    with _cache_lock:
        _cache[pair] = (now, result)
    return result
