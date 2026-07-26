from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol


@dataclass(frozen=True)
class BrokerOrderRequest:
    client_order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: Decimal
    limit_price: Decimal


@dataclass(frozen=True)
class BrokerOrderResult:
    external_order_id: str
    status: Literal["accepted", "cancelled"]


class BrokerAdapter(Protocol):
    name: str
    is_live: bool

    def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult: ...

    def cancel_order(self, external_order_id: str) -> BrokerOrderResult: ...
