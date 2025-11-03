from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from ..enums import Merchant


MERCHANT_LABELS: dict[Merchant, str] = {
    Merchant.AMAZON: "Amazon",
    Merchant.BEST_BUY: "Best Buy",
    Merchant.LOWES: "Lowe's",
    Merchant.WALMART: "Walmart",
    Merchant.HOME_DEPOT: "Home Depot",
}


def format_currency(amount: Decimal, currency: str) -> str:
    quantized = amount.quantize(Decimal("0.01"))
    return f"{currency} {quantized:,.2f}"


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "N/A"
    return value.strftime("%Y-%m-%d %H:%M")


def create_table_item(text: str, *, align_right: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if align_right:
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    else:
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    return item


def merchant_to_label(merchant: Merchant) -> str:
    return MERCHANT_LABELS.get(merchant, merchant.value.title())


def label_to_merchant(label: str) -> Merchant | None:
    for merchant, merchant_label in MERCHANT_LABELS.items():
        if merchant_label == label:
            return merchant
    return None
