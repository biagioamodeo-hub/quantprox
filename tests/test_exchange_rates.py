import json
from datetime import date
from io import BytesIO

from app.services import exchange_rates


class Response(BytesIO):
    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def test_exchange_rate_is_loaded_and_cached(monkeypatch) -> None:
    exchange_rates._cache.clear()
    calls = 0

    def fake_urlopen(request: object, timeout: int) -> Response:
        nonlocal calls
        calls += 1
        assert timeout == 5
        return Response(
            json.dumps(
                {
                    "date": "2026-07-24",
                    "base": "EUR",
                    "quote": "USD",
                    "rate": 1.1724,
                }
            ).encode()
        )

    monkeypatch.setattr(exchange_rates, "urlopen", fake_urlopen)

    first = exchange_rates.get_exchange_rate("eur", "usd")
    second = exchange_rates.get_exchange_rate("EUR", "USD")

    assert first == second
    assert first.rate_date == date(2026, 7, 24)
    assert str(first.rate) == "1.1724"
    assert calls == 1
