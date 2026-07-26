from uuid import NAMESPACE_URL, uuid5

from app.adapters.broker import (
    BrokerAdapter,
    BrokerOrderRequest,
    BrokerOrderResult,
)


class SandboxBrokerAdapter(BrokerAdapter):
    name = "sandbox"
    is_live = False

    def place_order(self, request: BrokerOrderRequest) -> BrokerOrderResult:
        external_order_id = str(
            uuid5(NAMESPACE_URL, f"quantprox:sandbox:{request.client_order_id}")
        )
        return BrokerOrderResult(
            external_order_id=external_order_id,
            status="accepted",
        )

    def cancel_order(self, external_order_id: str) -> BrokerOrderResult:
        return BrokerOrderResult(
            external_order_id=external_order_id,
            status="cancelled",
        )
