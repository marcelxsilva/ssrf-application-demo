"""
API administrativa INTERNA do FinanceHub (simulada) - SEM autenticação.

Representa o serviço interno do cenário AC03 (ex.: 10.0.0.15:8080): uma API de
suporte/administração que expõe o extrato de QUALQUER conta e que deveria estar
acessível apenas dentro da rede interna. Ela roda na rede interna do Docker e
NÃO é publicada para o host - a única forma de um usuário externo alcançá-la é
via SSRF através do backend.

Lê o MESMO banco PostgreSQL da aplicação, então vaza dados reais dos usuários.
"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://financehub:financehub@db:5432/financehub"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="FinanceHub - API Interna (simulada, SEM auth)")


@app.get("/", response_class=PlainTextResponse)
def root():
    return "API administrativa interna do FinanceHub - uso restrito à rede interna."


@app.post("/{full_path:path}")
async def collect(full_path: str, request: Request):
    """
    Recebe POSTs em qualquer caminho e responde 200. Representa um coletor interno
    (ou serviço de suporte) que passa a receber as notificações quando o webhook
    é apontado para a rede interna via SSRF - o dado sai da aplicação sem controle.
    """
    try:
        body = await request.json()
    except Exception:
        body = None
    return JSONResponse({"received": True, "path": "/" + full_path, "payload": body})


@app.get("/admin/accounts")
def list_accounts():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT username, full_name, account_number FROM users ORDER BY id")
        ).mappings().all()
    return {"accounts": [dict(r) for r in rows]}


@app.get("/admin/accounts/{username}/transactions")
def account_transactions(username: str):
    """Retorna o extrato completo de qualquer conta - SEM qualquer autenticação."""
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, username, full_name, account_number FROM users "
                 "WHERE username = :u"),
            {"u": username.lower()},
        ).mappings().first()
        if user is None:
            raise HTTPException(status_code=404, detail=f"conta '{username}' não encontrada")
        txs = conn.execute(
            text("SELECT tx_date, kind, description, amount FROM transactions "
                 "WHERE user_id = :uid ORDER BY tx_date DESC"),
            {"uid": user["id"]},
        ).mappings().all()
    balance = round(sum(float(t["amount"]) for t in txs), 2)
    return JSONResponse({
        "account": user["account_number"],
        "titular": user["full_name"],
        "username": user["username"],
        "balance": balance,
        "transactions": [
            {"date": t["tx_date"].isoformat(), "kind": t["kind"],
             "description": t["description"], "amount": float(t["amount"])}
            for t in txs
        ],
        "_aviso": "Endpoint interno SEM autenticação - dados expostos via SSRF.",
    })
