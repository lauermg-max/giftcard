from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict

from .enums import Merchant, TransactionType


def _normalize_amount(value: Decimal) -> Decimal:
    quantized = value.quantize(Decimal("0.01"))
    if quantized <= 0:
        raise ValueError("Amount must be greater than zero")
    return quantized


def cents_from_decimal(amount: Decimal) -> int:
    return int(amount * 100)


def decimal_from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GiftCardBase(ORMModel):
    code: str | None = Field(default=None, min_length=4, max_length=32)
    merchant: Merchant
    currency: str = Field(default="USD", min_length=3, max_length=3)
    expires_at: datetime | None = None
    extra_data: dict[str, Any] | None = None


class GiftCardCreate(GiftCardBase):
    initial_amount: Decimal = Field(..., examples=["100.00"])

    @field_validator("initial_amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return _normalize_amount(value)


class GiftCardUpdate(ORMModel):
    is_active: bool | None = None
    expires_at: datetime | None = None
    extra_data: dict[str, Any] | None = None


class GiftCardReload(ORMModel):
    amount: Decimal
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return _normalize_amount(value)


class GiftCardRedeem(ORMModel):
    amount: Decimal
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return _normalize_amount(value)


class GiftCardAdjustment(ORMModel):
    amount: Decimal
    note: str | None = None
    operation: Literal["increase", "decrease"]

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return _normalize_amount(value)


class GiftCardTransaction(ORMModel):
    id: int
    transaction_type: TransactionType
    amount: Decimal
    note: str | None
    created_at: datetime

    @classmethod
    def from_orm(cls, transaction: Any) -> "GiftCardTransaction":
        return cls(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=decimal_from_cents(transaction.amount_cents),
            note=transaction.note,
            created_at=transaction.created_at,
        )


class GiftCard(ORMModel):
    id: int
    code: str
    merchant: Merchant
    currency: str
    initial_amount: Decimal
    balance: Decimal
    is_active: bool
    expires_at: datetime | None
    extra_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, gift_card: Any) -> "GiftCard":
        return cls(
            id=gift_card.id,
            code=gift_card.code,
            merchant=gift_card.merchant,
            currency=gift_card.currency,
            initial_amount=decimal_from_cents(gift_card.initial_balance_cents),
            balance=decimal_from_cents(gift_card.balance_cents),
            is_active=gift_card.is_active,
            expires_at=gift_card.expires_at,
            extra_data=gift_card.extra_data,
            created_at=gift_card.created_at,
            updated_at=gift_card.updated_at,
        )


class GiftCardDetail(GiftCard):
    transactions: list[GiftCardTransaction]

    @classmethod
    def from_orm(cls, gift_card: Any) -> "GiftCardDetail":
        base = super().from_orm(gift_card)
        return cls(
            **base.model_dump(),
            transactions=[GiftCardTransaction.from_orm(tx) for tx in gift_card.transactions],
        )
