"""
Entrega de notificações ao webhook cadastrado pelo usuário.

Este é o ponto onde o SSRF realmente se materializa no FinanceHub: para notificar
uma movimentação, o servidor faz um POST para a URL que o usuário cadastrou. Se o
webhook foi salvo na versão VULNERÁVEL, o POST é feito sem validação; na versão
SEGURA, a URL passa pelo validador de 3 camadas antes do envio.
"""

from __future__ import annotations

import httpx

from .models import Transaction, User, WebhookDelivery
from .validator import OUTBOUND_TIMEOUT_SECONDS, validate_url


def deliver(db, user: User, tx: Transaction) -> WebhookDelivery:
    """Entrega a transação ao webhook do usuário e registra o resultado."""
    payload = {
        "event": "transaction.created",
        "account": user.account_number,
        "date": tx.tx_date.isoformat(),
        "kind": tx.kind,
        "description": tx.description,
        "amount": float(tx.amount),
    }
    rec = WebhookDelivery(
        user_id=user.id, url=user.webhook_url, mode=user.webhook_mode,
        description=tx.description, amount=tx.amount,
    )

    # Na versão segura, valida o destino antes de qualquer requisição de saída.
    if user.webhook_mode == "secure":
        verdict = validate_url(user.webhook_url)
        if not verdict.allowed:
            rec.ok = False
            rec.status_code = None
            rec.detail = f"Bloqueado: {verdict.layer_name}"
            db.add(rec)
            return rec

    follow = user.webhook_mode == "vulnerable"
    timeout = 10.0 if follow else OUTBOUND_TIMEOUT_SECONDS
    try:
        with httpx.Client(timeout=timeout, follow_redirects=follow, verify=False) as c:
            resp = c.post(user.webhook_url, json=payload)
        rec.ok = resp.status_code < 400
        rec.status_code = resp.status_code
        rec.detail = "Entregue" if rec.ok else f"HTTP {resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        rec.ok = False
        rec.detail = f"{type(exc).__name__}"
    db.add(rec)
    return rec
