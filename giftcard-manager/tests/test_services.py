from decimal import Decimal
from datetime import datetime, timedelta, timezone

import pytest

from giftcard_manager.enums import Merchant, TransactionType
from giftcard_manager.exceptions import GiftCardInsufficientFunds
from giftcard_manager.schemas import (
    GiftCardAdjustment,
    GiftCardCreate,
    GiftCardRedeem,
    GiftCardReload,
    GiftCardUpdate,
)


def issue_card(service, *, merchant=Merchant.AMAZON, amount="100.00", code="TESTCARD"):
    payload = GiftCardCreate(
        merchant=merchant,
        initial_amount=Decimal(amount),
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
    )
    return service.create_card(payload)


def test_create_card_initial_balance(service):
    card = issue_card(service)

    assert card.balance == Decimal("100.00")
    assert card.transactions
    assert card.transactions[0].transaction_type is TransactionType.ISSUE


def test_reload_and_redeem(service):
    card = issue_card(service, amount="50.00")

    service.reload_card(card.id, GiftCardReload(amount=Decimal("25.00"), note="Bonus"))
    updated = service.get_card(card.id)
    assert updated.balance == Decimal("75.00")

    service.redeem_card(card.id, GiftCardRedeem(amount=Decimal("20.00"), note="Sale"))
    updated = service.get_card(card.id)
    assert updated.balance == Decimal("55.00")


def test_redeem_insufficient_funds(service):
    card = issue_card(service, amount="10.00")

    with pytest.raises(GiftCardInsufficientFunds):
        service.redeem_card(card.id, GiftCardRedeem(amount=Decimal("15.00")))


def test_toggle_active(service):
    card = issue_card(service)

    service.update_card(card.id, GiftCardUpdate(is_active=False))
    updated = service.get_card(card.id)
    assert updated.is_active is False

    service.update_card(card.id, GiftCardUpdate(is_active=True))
    updated = service.get_card(card.id)
    assert updated.is_active is True


def test_manual_adjustment(service):
    card = issue_card(service, amount="80.00")

    service.adjust_card(card.id, GiftCardAdjustment(amount=Decimal("5.00"), operation="increase"))
    updated = service.get_card(card.id)
    assert updated.balance == Decimal("85.00")

    service.adjust_card(card.id, GiftCardAdjustment(amount=Decimal("10.00"), operation="decrease"))
    updated = service.get_card(card.id)
    assert updated.balance == Decimal("75.00")


def test_filter_by_merchant(service):
    issue_card(service, merchant=Merchant.AMAZON, code="AMZ1")
    issue_card(service, merchant=Merchant.WALMART, code="WMT1")

    amazon_cards = service.list_cards(merchant=Merchant.AMAZON)
    assert {card.code for card in amazon_cards} == {"AMZ1"}

    all_cards = service.list_cards()
    assert len(all_cards) == 2
