from __future__ import annotations

import enum

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .enums import Merchant, TransactionType


class GiftCard(Base):
    __tablename__ = "gift_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    merchant: Mapped[Merchant] = mapped_column(Enum(Merchant, native_enum=False), index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    initial_balance_cents: Mapped[int] = mapped_column(Integer)
    balance_cents: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transactions: Mapped[list["GiftCardTransaction"]] = relationship(
        "GiftCardTransaction", back_populates="gift_card", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("initial_balance_cents >= 0", name="ck_gift_cards_initial_balance_non_negative"),
        CheckConstraint("balance_cents >= 0", name="ck_gift_cards_balance_non_negative"),
    )


class GiftCardTransaction(Base):
    __tablename__ = "gift_card_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gift_card_id: Mapped[int] = mapped_column(ForeignKey("gift_cards.id", ondelete="CASCADE"), index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, native_enum=False))
    amount_cents: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    gift_card: Mapped["GiftCard"] = relationship("GiftCard", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_transactions_amount_non_negative"),
    )
