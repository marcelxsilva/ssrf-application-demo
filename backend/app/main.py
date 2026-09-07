"""
FinanceHub - API principal (backend com login real).

Reúne:
  - Autenticação (login JWT) e dados do usuário (transações próprias, com autorização)
  - A funcionalidade de webhooks em DUAS versões separadas por rota:
        /vulnerable/webhook/test  → SSRF explorável
        /secure/webhook/test      → protegida pelo validador de 3 camadas

O backend fica na rede de borda (acessível ao navegador) e também na rede interna
(onde estão db e internal-api). É essa dupla conexão que o SSRF explora:
o servidor alcança recursos internos que o navegador do usuário não acessa.
"""

import asyncio
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import generator
from .auth import create_token, get_current_user, verify_password
from .database import get_db
from .models import Transaction, User, WebhookDelivery
from .seed import seed
from .validator import DEFAULT_ALLOWLIST, OUTBOUND_TIMEOUT_SECONDS, validate_url

app = FastAPI(title="FinanceHub API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    # Aguarda o banco e popula (idempotente).
    for attempt in range(20):
        try:
            seed()
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[startup] aguardando o banco ({attempt + 1}/20): {exc}")
            time.sleep(2)
    # Gerador de transações em background (1 por usuário a cada TX_INTERVAL_SECONDS).
    asyncio.create_task(generator.run_forever())


@app.get("/")
def root():
    return {"status": "ok", "app": "FinanceHub API"}


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------


class LoginBody(BaseModel):
    username: str
    password: str


class WebhookBody(BaseModel):
    url: str


@app.post("/auth/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username.lower().strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name},
    }


@app.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "full_name": user.full_name,
        "account_number": user.account_number,
        "balance": user.balance,
    }


@app.get("/transactions")
def my_transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna SOMENTE as transações do próprio usuário autenticado (autorização)."""
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.tx_date.desc())
        .all()
    )
    return {
        "account_number": user.account_number,
        "balance": user.balance,
        "transactions": [t.to_dict() for t in txs],
    }


# ---------------------------------------------------------------------------
# Webhooks - configuração e helper de requisição de saída
# ---------------------------------------------------------------------------


@app.get("/config")
def config():
    return {
        "allowlist": sorted(DEFAULT_ALLOWLIST),
        "outbound_timeout_seconds": OUTBOUND_TIMEOUT_SECONDS,
    }


# --- Cadastro do webhook (recebe as notificações de transações) -----------


def _webhook_state(db: Session, user: User) -> dict:
    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.user_id == user.id)
        .order_by(WebhookDelivery.id.desc())
        .limit(15)
        .all()
    )
    return {
        "webhook_url": user.webhook_url,
        "webhook_mode": user.webhook_mode,
        "deliveries": [d.to_dict() for d in deliveries],
    }


@app.get("/webhook")
def get_webhook(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _webhook_state(db, user)


@app.post("/vulnerable/webhook/save")
def vulnerable_webhook_save(
    body: WebhookBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Salva a URL SEM validação - as notificações serão entregues como informado.
    user.webhook_url = body.url.strip()
    user.webhook_mode = "vulnerable"
    db.commit()
    return {"saved": True, "mode": "vulnerable", **_webhook_state(db, user)}


@app.post("/secure/webhook/save")
def secure_webhook_save(
    body: WebhookBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Valida antes de salvar: um destino inseguro nem chega a ser cadastrado.
    verdict = validate_url(body.url)
    if not verdict.allowed:
        return {
            "saved": False,
            "mode": "secure",
            "validation": {"performed": True, **verdict.to_dict()},
            **_webhook_state(db, user),
        }
    user.webhook_url = body.url.strip()
    user.webhook_mode = "secure"
    db.commit()
    return {"saved": True, "mode": "secure",
            "validation": {"performed": True, **verdict.to_dict()},
            **_webhook_state(db, user)}


async def _perform_request(url: str, *, follow_redirects: bool, timeout: float) -> dict:
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=follow_redirects, verify=False
        ) as client:
            resp = await client.get(url)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        try:
            body = resp.text
        except Exception:
            body = "<conteúdo binário>"
        if len(body) > 20000:
            body = body[:20000] + "\n... (truncado)"
        return {
            "reached": True,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": body,
            "elapsed_ms": elapsed,
        }
    except httpx.ConnectError as exc:
        return {"reached": False, "error": "ConnectError", "detail": str(exc)}
    except httpx.TimeoutException as exc:
        return {"reached": False, "error": "Timeout", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"reached": False, "error": type(exc).__name__, "detail": str(exc)}


# ---------------------------------------------------------------------------
# VERSÃO VULNERÁVEL - sem validação (SSRF explorável)
# ---------------------------------------------------------------------------


@app.post("/vulnerable/webhook/test")
async def vulnerable_webhook(body: WebhookBody, user: User = Depends(get_current_user)):
    result = await _perform_request(body.url, follow_redirects=True, timeout=5.0)
    return {
        "mode": "vulnerable",
        "url": body.url,
        "requested_by": user.username,
        "validation": {"performed": False},
        "request": result,
    }


# ---------------------------------------------------------------------------
# VERSÃO SEGURA - validador de 3 camadas
# ---------------------------------------------------------------------------


@app.post("/secure/webhook/test")
async def secure_webhook(body: WebhookBody, user: User = Depends(get_current_user)):
    verdict = validate_url(body.url)
    if not verdict.allowed:
        return {
            "mode": "secure",
            "url": body.url,
            "requested_by": user.username,
            "validation": {"performed": True, **verdict.to_dict()},
            "request": {
                "reached": False,
                "error": "Blocked",
                "detail": "Requisição de saída não realizada (bloqueada na validação).",
            },
        }
    result = await _perform_request(
        body.url, follow_redirects=False, timeout=OUTBOUND_TIMEOUT_SECONDS
    )
    return {
        "mode": "secure",
        "url": body.url,
        "requested_by": user.username,
        "validation": {"performed": True, **verdict.to_dict()},
        "request": result,
    }
