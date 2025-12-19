from ninja import Schema
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class CurrencySchema(Schema):
    code: str
    rate: Decimal

    class Config:
        from_attributes = True


class CurrencyStateSchema(Schema):
    id: UUID
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CurrencyStateDetailSchema(Schema):
    id: UUID
    source: str
    created_at: datetime
    updated_at: datetime
    currencies: dict[str, float]

    class Config:
        from_attributes = True


class CurrencyRateSchema(Schema):
    code: str
    rate: Decimal
