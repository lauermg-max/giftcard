from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .enums import Merchant, TransactionType
from .exceptions import (
    GiftCardCodeGenerationError,
    GiftCardDuplicateCode,
    GiftCardError,
    GiftCardExpired,
    GiftCardInactive,
    GiftCardInsufficientFunds,
    GiftCardNotFound,
)
from .models import GiftCard as GiftCardModel
from .models import GiftCardTransaction as GiftCardTransactionModel
from .schemas import (
    GiftCardAdjustment,
    GiftCardCreate,
    GiftCardRedeem,
    GiftCardReload,
    GiftCardUpdate,
)

CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 12


def _normalize_code(raw_code: str) -> str:
    return raw_code.strip().upper()


def _to_cents(amount: Decimal) -> int:
    return int((amount * 100).to_integral_value())


def _ensure_card_exists(db: Session, gift_card_id: int) -> GiftCardModel:
    card = db.get(GiftCardModel, gift_card_id)
    if not card:
        raise GiftCardNotFound()
    return card


def _ensure_card_available(card: GiftCardModel) -> None:
    if not card.is_active:
        raise GiftCardInactive()
    if card.expires_at and card.expires_at <= datetime.now(timezone.utc):
        raise GiftCardExpired()


def _create_transaction(
    card: GiftCardModel,
    transaction_type: TransactionType,
    amount_cents: int,
    note: str | None = None,
) -> GiftCardTransactionModel:
    transaction = GiftCardTransactionModel(
        gift_card=card,
        transaction_type=transaction_type,
        amount_cents=amount_cents,
        note=note,
    )
    card.transactions.append(transaction)
    return transaction


def _generate_unique_code(db: Session, desired_code: str | None = None) -> str:
    if desired_code:
        code = _normalize_code(desired_code)
        existing = db.scalar(select(GiftCardModel.id).where(GiftCardModel.code == code))
        if existing:
            raise GiftCardDuplicateCode()
        return code

    for _ in range(20):
        candidate = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        exists = db.scalar(select(GiftCardModel.id).where(GiftCardModel.code == candidate))
        if not exists:
            return candidate

    raise GiftCardCodeGenerationError()


def create_gift_card(db: Session, payload: GiftCardCreate) -> GiftCardModel:
    initial_cents = _to_cents(payload.initial_amount)
    code = _generate_unique_code(db, payload.code)

    card = GiftCardModel(
        code=code,
        merchant=payload.merchant,
        currency=payload.currency,
        initial_balance_cents=initial_cents,
        balance_cents=initial_cents,
        expires_at=payload.expires_at,
        extra_data=payload.extra_data,
    )
    _create_transaction(card, TransactionType.ISSUE, initial_cents, note="Initial issuance")

    db.add(card)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise GiftCardError("Failed to create gift card") from exc

    db.refresh(card)
    return card


def list_gift_cards(
    db: Session,
    *,
    merchant: Merchant | None = None,
    is_active: bool | None = None,
) -> list[GiftCardModel]:
    query: Select[tuple[GiftCardModel]] = select(GiftCardModel)
    if merchant is not None:
        query = query.where(GiftCardModel.merchant == merchant)
    if is_active is not None:
        query = query.where(GiftCardModel.is_active == is_active)

    query = query.order_by(GiftCardModel.created_at.desc())
    return list(db.scalars(query).all())


def get_gift_card(db: Session, gift_card_id: int) -> GiftCardModel:
    return _ensure_card_exists(db, gift_card_id)


def get_gift_card_by_code(db: Session, code: str) -> GiftCardModel:
    normalized = _normalize_code(code)
    card = db.scalar(select(GiftCardModel).where(GiftCardModel.code == normalized))
    if not card:
        raise GiftCardNotFound()
    return card


def update_gift_card(db: Session, gift_card_id: int, payload: GiftCardUpdate) -> GiftCardModel:
    card = _ensure_card_exists(db, gift_card_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "is_active" in update_data:
        card.is_active = update_data["is_active"]
    if "expires_at" in update_data:
        card.expires_at = update_data["expires_at"]
    if "extra_data" in update_data:
        card.extra_data = update_data["extra_data"]

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def reload_gift_card(db: Session, gift_card_id: int, payload: GiftCardReload) -> GiftCardModel:
    card = _ensure_card_exists(db, gift_card_id)
    _ensure_card_available(card)

    amount_cents = _to_cents(payload.amount)
    card.balance_cents += amount_cents
    _create_transaction(card, TransactionType.RELOAD, amount_cents, note=payload.note)

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def redeem_gift_card(db: Session, gift_card_id: int, payload: GiftCardRedeem) -> GiftCardModel:
    card = _ensure_card_exists(db, gift_card_id)
    _ensure_card_available(card)

    amount_cents = _to_cents(payload.amount)
    if amount_cents > card.balance_cents:
        raise GiftCardInsufficientFunds()

    card.balance_cents -= amount_cents
    _create_transaction(card, TransactionType.REDEEM, amount_cents, note=payload.note)

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def adjust_gift_card(db: Session, gift_card_id: int, payload: GiftCardAdjustment) -> GiftCardModel:
    card = _ensure_card_exists(db, gift_card_id)
    _ensure_card_available(card)

    amount_cents = _to_cents(payload.amount)

    if payload.operation == "increase":
        card.balance_cents += amount_cents
    else:
        if amount_cents > card.balance_cents:
            raise GiftCardInsufficientFunds("Adjustment exceeds current balance")
        card.balance_cents -= amount_cents

    note = payload.note or f"Balance {payload.operation} adjustment"
    _create_transaction(card, TransactionType.ADJUSTMENT, amount_cents, note=note)

    db.add(card)
    db.commit()
    db.refresh(card)
    return card
