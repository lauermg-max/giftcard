from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from ..enums import Merchant
from ..schemas import GiftCardAdjustment
from .utils import MERCHANT_LABELS


def _decimal_from_spinbox(spinbox: QDoubleSpinBox) -> Decimal:
    return Decimal(f"{spinbox.value():.2f}")


class IssueGiftCardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Issue New Gift Card")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.merchant_combo = QComboBox()
        for merchant, label in MERCHANT_LABELS.items():
            self.merchant_combo.addItem(label, merchant)
        form.addRow("Merchant", self.merchant_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMinimum(1.00)
        self.amount_spin.setMaximum(1000000.00)
        self.amount_spin.setValue(100.00)
        form.addRow("Initial Amount", self.amount_spin)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Optional custom code")
        form.addRow("Gift Card Code", self.code_input)

        expiry_layout = QHBoxLayout()
        self.expiry_checkbox = QCheckBox("Set expiration date")
        self.expiry_checkbox.toggled.connect(self._toggle_expiry)
        expiry_layout.addWidget(self.expiry_checkbox)

        self.expiry_edit = QDateEdit()
        self.expiry_edit.setCalendarPopup(True)
        self.expiry_edit.setDate(QDate.currentDate().addYears(1))
        self.expiry_edit.setEnabled(False)
        expiry_layout.addWidget(self.expiry_edit)
        form.addRow("Expires", expiry_layout)

        layout.addLayout(form)

        self.extra_notes = QTextEdit()
        self.extra_notes.setPlaceholderText("Optional notes about this gift card")
        layout.addWidget(self.extra_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_expiry(self, checked: bool) -> None:
        self.expiry_edit.setEnabled(checked)

    def get_payload_kwargs(self) -> dict:
        merchant: Merchant = self.merchant_combo.currentData()
        amount = _decimal_from_spinbox(self.amount_spin)
        code = self.code_input.text().strip() or None
        extra_data = None
        notes = self.extra_notes.toPlainText().strip()
        if notes:
            extra_data = {"notes": notes}

        expires_at: datetime | None = None
        if self.expiry_checkbox.isChecked():
            qdate = self.expiry_edit.date()
            expires_at = datetime(qdate.year(), qdate.month(), qdate.day(), 23, 59, 59, tzinfo=timezone.utc)

        return {
            "merchant": merchant,
            "initial_amount": amount,
            "code": code,
            "expires_at": expires_at,
            "extra_data": extra_data,
        }


class AmountDialog(QDialog):
    def __init__(self, title: str, *, default_amount: float = 25.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMinimum(1.00)
        self.amount_spin.setMaximum(1000000.00)
        self.amount_spin.setValue(default_amount)
        form.addRow("Amount", self.amount_spin)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Optional note")
        form.addRow("Note", self.note_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_amount(self) -> Decimal:
        return _decimal_from_spinbox(self.amount_spin)

    def get_note(self) -> str | None:
        text = self.note_input.toPlainText().strip()
        return text or None


class AdjustBalanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Balance")

        layout = QVBoxLayout(self)

        amount_group = QGroupBox("Adjustment")
        amount_layout = QFormLayout()

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMinimum(1.00)
        self.amount_spin.setMaximum(1000000.00)
        self.amount_spin.setValue(10.00)
        amount_layout.addRow("Amount", self.amount_spin)

        radio_layout = QHBoxLayout()
        self.increase_radio = QRadioButton("Increase")
        self.decrease_radio = QRadioButton("Decrease")
        self.increase_radio.setChecked(True)
        radio_layout.addWidget(self.increase_radio)
        radio_layout.addWidget(self.decrease_radio)
        amount_layout.addRow(QLabel("Operation"), radio_layout)

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Optional note")
        amount_layout.addRow("Note", self.note_input)

        amount_group.setLayout(amount_layout)
        layout.addWidget(amount_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_payload(self) -> GiftCardAdjustment:
        operation: Literal["increase", "decrease"] = "increase" if self.increase_radio.isChecked() else "decrease"
        note = self.note_input.toPlainText().strip() or None
        amount = _decimal_from_spinbox(self.amount_spin)
        return GiftCardAdjustment(amount=amount, note=note, operation=operation)
