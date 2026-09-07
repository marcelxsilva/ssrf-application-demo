"""Modelos de dados do FinanceHub: usuários, transações e webhooks."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    account_number: Mapped[str] = mapped_column(String(20), unique=True)

    # Webhook cadastrado pelo usuário para receber notificações de movimentações.
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Versão sob a qual o webhook foi salvo/entregue: "vulnerable" ou "secure".
    webhook_mode: Mapped[str] = mapped_column(String(20), default="secure")

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def balance(self) -> float:
        return round(sum(float(t.amount) for t in self.transactions), 2)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tx_date: Mapped[date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(20))  # credito | debito | transferencia
    description: Mapped[str] = mapped_column(String(160))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))  # negativo = saída

    user: Mapped["User"] = relationship(back_populates="transactions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.tx_date.isoformat(),
            "kind": self.kind,
            "description": self.description,
            "amount": float(self.amount),
        }


class WebhookDelivery(Base):
    """Registro de cada tentativa de entrega de uma notificação ao webhook."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    url: Mapped[str] = mapped_column(String(500))
    mode: Mapped[str] = mapped_column(String(20))
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(String(160), default="")  # da transação
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    user: Mapped["User"] = relationship(back_populates="deliveries")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "at": self.created_at.strftime("%H:%M:%S"),
            "url": self.url,
            "mode": self.mode,
            "ok": self.ok,
            "status_code": self.status_code,
            "detail": self.detail,
            "description": self.description,
            "amount": float(self.amount),
        }
