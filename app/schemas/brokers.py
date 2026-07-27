from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BrokerSubmissionRead(BaseModel):
    id: int
    order_id: int
    provider: str
    external_order_id: str
    status: Literal["accepted", "cancelled"]
    submitted_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevolutDemoPurchaseCreate(BaseModel):
    asset_type: Literal["stock", "bond", "government_bond", "crypto", "etf", "fund"]
    asset_label: str = Field(min_length=1, max_length=64)
    virtual_balance: Decimal = Field(ge=100, le=1000000)
    amount: Decimal = Field(gt=0, le=1000000)
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class RevolutDemoPurchaseRead(BaseModel):
    provider: Literal["revolut_demo"] = "revolut_demo"
    account_label: str = "Revolut Demo"
    reference: str
    status: Literal["completed"] = "completed"
    asset_type: str
    asset_label: str
    gross_amount: Decimal
    simulated_fee: Decimal
    total_debit: Decimal
    remaining_balance: Decimal
    currency: str
    executed_at: datetime
    disclaimer: str = (
        "Operazione esclusivamente virtuale: non è collegata a Revolut, "
        "non trasferisce denaro e non acquista strumenti reali."
    )


class RevolutDemoCardCreate(BaseModel):
    account_label: str = Field(default="Revolut Demo", min_length=1, max_length=64)
    virtual_balance: Decimal = Field(ge=100, le=1000000)
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class RevolutDemoCardRead(BaseModel):
    provider: Literal["revolut_demo"] = "revolut_demo"
    card_id: str
    account_label: str
    masked_number: str
    network: Literal["VISA"] = "VISA"
    linked: Literal[True] = True
    spending_limit: Decimal
    currency: str
    disclaimer: str = (
        "Carta esclusivamente virtuale e dimostrativa; non è una carta Revolut "
        "reale e non può effettuare pagamenti."
    )
