"""
Gerador de transações em background.

A cada N segundos (padrão 120 = 2 min) insere UMA transação aleatória para cada
usuário existente na base, deixando os extratos "vivos" durante a demonstração.
"""

import asyncio
import os
import random
from datetime import date

from .database import SessionLocal
from .delivery import deliver
from .models import Transaction, User

# limita quantas entregas guardamos por usuário (evita crescer sem limite)
MAX_DELIVERIES_PER_USER = 15

INTERVAL_SECONDS = int(os.environ.get("TX_INTERVAL_SECONDS", "120"))

# Modelos de transação: (tipo, descrição, faixa de valor). Débitos são negativos.
CREDITS = [
    ("credito", "Depósito", (50, 900)),
    ("credito", "Estorno de compra", (10, 200)),
    ("credito", "Rendimento", (1, 40)),
    ("transferencia", "PIX recebido", (20, 600)),
]
DEBITS = [
    ("debito", "Compra no cartão", (15, 400)),
    ("debito", "Mercado", (30, 350)),
    ("debito", "Restaurante", (25, 180)),
    ("debito", "Assinatura", (10, 60)),
    ("transferencia", "PIX enviado", (20, 500)),
]


def _random_transaction() -> dict:
    # ~40% créditos, 60% débitos, para os saldos variarem de forma realista.
    kind, desc, (lo, hi) = random.choice(CREDITS if random.random() < 0.4 else DEBITS)
    amount = round(random.uniform(lo, hi), 2)
    if kind == "debito" or desc == "PIX enviado":
        amount = -amount
    return {"kind": kind, "description": desc, "amount": amount}


def generate_once() -> int:
    """
    Insere uma transação aleatória para cada usuário e, se ele tiver um webhook
    cadastrado, entrega a notificação. Retorna quantas transações criou.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            data = _random_transaction()
            tx = Transaction(
                user_id=u.id, tx_date=date.today(),
                kind=data["kind"], description=data["description"], amount=data["amount"],
            )
            db.add(tx)
            db.flush()  # garante tx populada antes da entrega
            if u.webhook_url:
                deliver(db, u, tx)
                _trim_deliveries(db, u.id)
        db.commit()
        return len(users)
    finally:
        db.close()


def _trim_deliveries(db, user_id: int):
    from .models import WebhookDelivery
    ids = [d.id for d in db.query(WebhookDelivery.id)
           .filter(WebhookDelivery.user_id == user_id)
           .order_by(WebhookDelivery.id.desc()).offset(MAX_DELIVERIES_PER_USER).all()]
    if ids:
        db.query(WebhookDelivery).filter(WebhookDelivery.id.in_(ids)).delete(
            synchronize_session=False)


async def run_forever():
    """Loop em background: aguarda o intervalo e gera transações, sem derrubar a API."""
    print(f"[generator] ativo - 1 transação por usuário a cada {INTERVAL_SECONDS}s")
    while True:
        await asyncio.sleep(INTERVAL_SECONDS)
        try:
            n = await asyncio.to_thread(generate_once)
            print(f"[generator] {n} transações geradas.")
        except Exception as exc:  # noqa: BLE001 - não deve interromper o loop
            print(f"[generator] falha ao gerar transações: {exc}")
