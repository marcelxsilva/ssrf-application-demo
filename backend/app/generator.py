"""
Gerador de transações em background.

Roda RUNS_PER_DAY vezes por dia (padrão 5) e, em cada rodada, insere para cada
usuário um crédito e, opcionalmente, um débito menor que o crédito - o saldo
sempre tende a subir, mesmo com saídas.
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

SECONDS_PER_DAY = 86400
RUNS_PER_DAY = int(os.environ.get("TX_RUNS_PER_DAY", "5"))
INTERVAL_SECONDS = int(
    os.environ.get("TX_INTERVAL_SECONDS", str(SECONDS_PER_DAY // RUNS_PER_DAY))
)

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

# Teto do débito como fração do crédito da mesma rodada: garante que a entrada
# cobre a saída e o saldo do usuário fica sempre positivo ao longo do tempo.
MAX_DEBIT_RATIO = 0.7


def _random_credit() -> dict:
    kind, desc, (lo, hi) = random.choice(CREDITS)
    amount = round(random.uniform(lo, hi), 2)
    return {"kind": kind, "description": desc, "amount": amount}


def _random_debit(max_amount: float) -> dict | None:
    if max_amount <= 0 or random.random() >= 0.6:
        return None
    kind, desc, (lo, hi) = random.choice(DEBITS)
    hi = min(hi, max_amount)
    lo = min(lo, hi)
    amount = round(random.uniform(lo, hi), 2)
    return {"kind": kind, "description": desc, "amount": -amount}


def generate_once() -> int:
    """
    Insere, para cada usuário, um crédito e um débito opcional (sempre menor que o
    crédito) e entrega webhook se houver. Retorna quantas transações criou.
    """
    db = SessionLocal()
    created = 0
    try:
        users = db.query(User).all()
        for u in users:
            credit = _random_credit()
            debit = _random_debit(credit["amount"] * MAX_DEBIT_RATIO)
            for data in filter(None, [credit, debit]):
                tx = Transaction(
                    user_id=u.id, tx_date=date.today(),
                    kind=data["kind"], description=data["description"], amount=data["amount"],
                )
                db.add(tx)
                db.flush()  # garante tx populada antes da entrega
                created += 1
                if u.webhook_url:
                    deliver(db, u, tx)
                    _trim_deliveries(db, u.id)
        db.commit()
        return created
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
    print(f"[generator] ativo - {RUNS_PER_DAY}x por dia (a cada {INTERVAL_SECONDS}s)")
    while True:
        await asyncio.sleep(INTERVAL_SECONDS)
        try:
            n = await asyncio.to_thread(generate_once)
            print(f"[generator] {n} transações geradas.")
        except Exception as exc:  # noqa: BLE001 - não deve interromper o loop
            print(f"[generator] falha ao gerar transações: {exc}")
