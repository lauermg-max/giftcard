from __future__ import annotations

from typing import Iterable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ..enums import Merchant
from ..exceptions import GiftCardError
from ..schemas import GiftCard, GiftCardCreate, GiftCardDetail, GiftCardRedeem, GiftCardReload, GiftCardUpdate
from ..services import GiftCardService
from .dialogs import AdjustBalanceDialog, AmountDialog, IssueGiftCardDialog
from .utils import create_table_item, format_currency, format_datetime, merchant_to_label


class MainWindow(QMainWindow):
    def __init__(self, service: GiftCardService | None = None):
        super().__init__()
        self.service = service or GiftCardService()
        self.cards: list[GiftCard] = []
        self.selected_card: GiftCardDetail | None = None

        self.setWindowTitle("Gift Card Manager")
        self.resize(1100, 720)

        self._build_ui()
        self._create_menu()
        self.refresh_cards()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        filters_layout = QHBoxLayout()

        self.merchant_filter = QComboBox()
        self.merchant_filter.addItem("All Merchants", None)
        for merchant in Merchant:
            self.merchant_filter.addItem(merchant_to_label(merchant), merchant)
        self.merchant_filter.currentIndexChanged.connect(self.refresh_cards)
        filters_layout.addWidget(QLabel("Merchant:"))
        filters_layout.addWidget(self.merchant_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Active", "Inactive", "All"])
        self.status_filter.currentIndexChanged.connect(self.refresh_cards)
        filters_layout.addWidget(QLabel("Status:"))
        filters_layout.addWidget(self.status_filter)

        filters_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_cards)
        filters_layout.addWidget(self.refresh_button)

        main_layout.addLayout(filters_layout)

        content_layout = QHBoxLayout()

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Code", "Merchant", "Balance", "Initial", "Status", "Expires"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self._handle_row_selected)
        content_layout.addWidget(self.table, stretch=3)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self._build_details_group())
        right_panel.addWidget(self._build_transactions_group())
        content_layout.addLayout(right_panel, stretch=2)

        main_layout.addLayout(content_layout)

        buttons_layout = QHBoxLayout()

        self.issue_button = QPushButton("Issue Card")
        self.issue_button.clicked.connect(self.issue_card)
        buttons_layout.addWidget(self.issue_button)

        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_card)
        buttons_layout.addWidget(self.reload_button)

        self.redeem_button = QPushButton("Redeem")
        self.redeem_button.clicked.connect(self.redeem_card)
        buttons_layout.addWidget(self.redeem_button)

        self.adjust_button = QPushButton("Adjust Balance")
        self.adjust_button.clicked.connect(self.adjust_balance)
        buttons_layout.addWidget(self.adjust_button)

        self.toggle_button = QPushButton("Deactivate")
        self.toggle_button.clicked.connect(self.toggle_active)
        buttons_layout.addWidget(self.toggle_button)

        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout)

        self.setCentralWidget(central_widget)
        self._update_action_states()

    def _build_details_group(self) -> QGroupBox:
        group = QGroupBox("Gift Card Details")
        layout = QFormLayout()

        self.code_label = QLabel("N/A")
        layout.addRow("Code:", self.code_label)

        self.merchant_label = QLabel("N/A")
        layout.addRow("Merchant:", self.merchant_label)

        self.balance_label = QLabel("N/A")
        layout.addRow("Balance:", self.balance_label)

        self.initial_label = QLabel("N/A")
        layout.addRow("Initial Amount:", self.initial_label)

        self.status_label = QLabel("N/A")
        layout.addRow("Status:", self.status_label)

        self.expires_label = QLabel("N/A")
        layout.addRow("Expires:", self.expires_label)

        self.updated_label = QLabel("N/A")
        layout.addRow("Updated:", self.updated_label)

        group.setLayout(layout)
        return group

    def _build_transactions_group(self) -> QGroupBox:
        group = QGroupBox("Recent Transactions")
        layout = QVBoxLayout()

        self.transactions_table = QTableWidget(0, 4)
        self.transactions_table.setHorizontalHeaderLabels(["Type", "Amount", "Note", "Date"])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.setSelectionMode(QTableWidget.NoSelection)

        layout.addWidget(self.transactions_table)
        group.setLayout(layout)
        return group

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        export_action = QAction("Export Summary", self)
        export_action.triggered.connect(self.export_summary)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(quit_action)

    def _update_action_states(self) -> None:
        has_selection = self.selected_card is not None
        for button in (self.reload_button, self.redeem_button, self.adjust_button, self.toggle_button):
            button.setEnabled(has_selection)

        if not has_selection:
            self.toggle_button.setText("Deactivate")
        elif self.selected_card.is_active:
            self.toggle_button.setText("Deactivate")
        else:
            self.toggle_button.setText("Activate")

    def refresh_cards(self) -> None:
        merchant = self.merchant_filter.currentData()
        status_text = self.status_filter.currentText()
        is_active = None
        if status_text == "Active":
            is_active = True
        elif status_text == "Inactive":
            is_active = False

        try:
            cards = self.service.list_cards(merchant=merchant, is_active=is_active)
        except GiftCardError as exc:
            self._show_error(str(exc))
            return

        self.cards = cards
        self._populate_table(cards)
        self.selected_card = None
        self._clear_details()
        self._update_action_states()

    def _populate_table(self, cards: Iterable[GiftCard]) -> None:
        self.table.setRowCount(0)
        for row, card in enumerate(cards):
            self.table.insertRow(row)
            self.table.setItem(row, 0, create_table_item(card.code))
            self.table.setItem(row, 1, create_table_item(merchant_to_label(card.merchant)))
            self.table.setItem(row, 2, create_table_item(format_currency(card.balance, card.currency), align_right=True))
            self.table.setItem(row, 3, create_table_item(format_currency(card.initial_amount, card.currency), align_right=True))
            status = "Active" if card.is_active else "Inactive"
            self.table.setItem(row, 4, create_table_item(status))
            self.table.setItem(row, 5, create_table_item(format_datetime(card.expires_at)))

    def _handle_row_selected(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self.cards):
            return
        card = self.cards[row]
        try:
            self.selected_card = self.service.get_card(card.id)
        except GiftCardError as exc:
            self._show_error(str(exc))
            return

        self._render_details()
        self._render_transactions()
        self._update_action_states()

    def _render_details(self) -> None:
        if not self.selected_card:
            self._clear_details()
            return

        card = self.selected_card
        self.code_label.setText(card.code)
        self.merchant_label.setText(merchant_to_label(card.merchant))
        self.balance_label.setText(format_currency(card.balance, card.currency))
        self.initial_label.setText(format_currency(card.initial_amount, card.currency))
        self.status_label.setText("Active" if card.is_active else "Inactive")
        self.expires_label.setText(format_datetime(card.expires_at))
        self.updated_label.setText(format_datetime(card.updated_at))

    def _render_transactions(self) -> None:
        self.transactions_table.setRowCount(0)
        if not self.selected_card:
            return

        transactions = sorted(
            self.selected_card.transactions,
            key=lambda tx: tx.created_at,
            reverse=True,
        )

        for row, tx in enumerate(transactions):
            self.transactions_table.insertRow(row)
            self.transactions_table.setItem(row, 0, create_table_item(tx.transaction_type.value.title()))
            self.transactions_table.setItem(row, 1, create_table_item(format_currency(tx.amount, self.selected_card.currency), align_right=True))
            self.transactions_table.setItem(row, 2, create_table_item(tx.note or ""))
            self.transactions_table.setItem(row, 3, create_table_item(format_datetime(tx.created_at)))

    def _clear_details(self) -> None:
        for label in (
            self.code_label,
            self.merchant_label,
            self.balance_label,
            self.initial_label,
            self.status_label,
            self.expires_label,
            self.updated_label,
        ):
            label.setText("N/A")
        self.transactions_table.setRowCount(0)

    def issue_card(self) -> None:
        dialog = IssueGiftCardDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        try:
            payload = GiftCardCreate(**dialog.get_payload_kwargs())
            created_card = self.service.create_card(payload)
            card_id = created_card.id
            self.refresh_cards()
            self._select_card_by_id(card_id)
        except GiftCardError as exc:
            self._show_error(str(exc))

    def reload_card(self) -> None:
        card = self.selected_card
        if not card:
            return

        dialog = AmountDialog("Reload Gift Card", default_amount=50.0)
        if dialog.exec() != QDialog.Accepted:
            return

        try:
            payload = GiftCardReload(amount=dialog.get_amount(), note=dialog.get_note())
            self.service.reload_card(card.id, payload)
            self.refresh_cards()
            self._select_card_by_id(card.id)
        except GiftCardError as exc:
            self._show_error(str(exc))

    def redeem_card(self) -> None:
        card = self.selected_card
        if not card:
            return

        dialog = AmountDialog("Redeem Gift Card", default_amount=25.0)
        if dialog.exec() != QDialog.Accepted:
            return

        try:
            payload = GiftCardRedeem(amount=dialog.get_amount(), note=dialog.get_note())
            self.service.redeem_card(card.id, payload)
            self.refresh_cards()
            self._select_card_by_id(card.id)
        except GiftCardError as exc:
            self._show_error(str(exc))

    def adjust_balance(self) -> None:
        card = self.selected_card
        if not card:
            return

        dialog = AdjustBalanceDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        try:
            payload = dialog.get_payload()
            self.service.adjust_card(card.id, payload)
            self.refresh_cards()
            self._select_card_by_id(card.id)
        except GiftCardError as exc:
            self._show_error(str(exc))

    def toggle_active(self) -> None:
        card = self.selected_card
        if not card:
            return

        desired_state = not card.is_active
        status_text = "activate" if desired_state else "deactivate"

        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to {status_text} gift card {card.code}?",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            payload = GiftCardUpdate(is_active=desired_state)
            self.service.update_card(card.id, payload)
            self.refresh_cards()
            self._select_card_by_id(card.id)
        except GiftCardError as exc:
            self._show_error(str(exc))

    def export_summary(self) -> None:
        if not self.cards:
            QMessageBox.information(self, "Export Summary", "There are no gift cards to export.")
            return

        rows = [
            [
                card.code,
                merchant_to_label(card.merchant),
                f"{card.currency} {card.balance:,.2f}",
                "Active" if card.is_active else "Inactive",
                format_datetime(card.expires_at),
            ]
            for card in self.cards
        ]

        summary = "Code,Merchant,Balance,Status,Expires\n" + "\n".join(",".join(row) for row in rows)

        QMessageBox.information(
            self,
            "Export Summary",
            "Copy the summary below into your spreadsheet tool:\n\n" + summary,
        )

    def _select_card_by_id(self, card_id: int) -> None:
        for row, card in enumerate(self.cards):
            if card.id == card_id:
                self.table.selectRow(row)
                self._handle_row_selected(row, 0)
                return

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)


def run() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


__all__ = ["MainWindow", "run"]
