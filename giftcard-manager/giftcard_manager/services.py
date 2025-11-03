from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from . import crud, database
from .enums import Merchant
from .exceptions import GiftCardError
from .schemas import (
    GiftCard,
    GiftCardAdjustment,
    GiftCardCreate,
    GiftCardDetail,
    GiftCardRedeem,
    GiftCardReload,
    GiftCardUpdate,
)


@contextmanager
def _session_scope(session_factory=database.SessionLocal) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


class GiftCardService:
    def list_cards(self, *, merchant: Merchant | None = None, is_active: bool | None = None) -> list[GiftCard]:
        with _session_scope() as session:
            cards = crud.list_gift_cards(session, merchant=merchant, is_active=is_active)
            return [GiftCard.from_orm(card) for card in cards]

    def get_card(self, gift_card_id: int) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.get_gift_card(session, gift_card_id)
            return GiftCardDetail.from_orm(card)

    def get_card_by_code(self, code: str) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.get_gift_card_by_code(session, code)
            return GiftCardDetail.from_orm(card)

    def create_card(self, payload: GiftCardCreate) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.create_gift_card(session, payload)
            return GiftCardDetail.from_orm(card)

    def update_card(self, gift_card_id: int, payload: GiftCardUpdate) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.update_gift_card(session, gift_card_id, payload)
            return GiftCardDetail.from_orm(card)

    def reload_card(self, gift_card_id: int, payload: GiftCardReload) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.reload_gift_card(session, gift_card_id, payload)
            return GiftCardDetail.from_orm(card)

    def redeem_card(self, gift_card_id: int, payload: GiftCardRedeem) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.redeem_gift_card(session, gift_card_id, payload)
            return GiftCardDetail.from_orm(card)

    def adjust_card(self, gift_card_id: int, payload: GiftCardAdjustment) -> GiftCardDetail:
        with _session_scope() as session:
            card = crud.adjust_gift_card(session, gift_card_id, payload)
            return GiftCardDetail.from_orm(card)


__all__ = [
    "GiftCardService",
    "GiftCardError",
    "GiftCard",
    "GiftCardDetail",
]
