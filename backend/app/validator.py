"""
Módulo de validação segura de URLs - defesa contra SSRF (FinanceHub).

Implementa a arquitetura de defesa em profundidade descrita na AC03, em três
camadas complementares aplicadas EM SÉRIE antes de qualquer requisição de saída:

    Camada 1 - Validação de esquema e estrutura da URL
    Camada 2 - Resolução DNS e verificação de IP de destino
    Camada 3 - Allowlist de domínios (controles de transporte ficam no cliente)

O princípio central é: basta uma camada reprovar para que a URL seja bloqueada
e NENHUMA requisição de saída seja realizada. Cada bloqueio registra qual camada
o originou e o motivo, permitindo auditoria e a geração de resultados (item 6).

Referências: OWASP SSRF Prevention Cheat Sheet; OWASP Top 10 A10:2021; RFC 1918.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urlsplit

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Camada 1 - apenas HTTP/HTTPS são aceitos. Qualquer outro esquema é recusado.
ALLOWED_SCHEMES = {"http", "https"}

# Camada 3 - allowlist de domínios de parceiros autorizados a receber webhooks.
# Em produção seria configurável por ambiente (dev/homolog/prod) e por cliente.
# Para a demo, `example.com` representa um parceiro externo legítimo.
DEFAULT_ALLOWLIST = {
    "example.com",
    "www.example.com",
    "hooks.parceiro-financehub.com",
    # Receptor de webhook público usado como "parceiro autorizado" na demo:
    # aceita POST e devolve 200 ecoando o corpo, evidenciando a entrega.
    "httpbin.org",
    "686c60dc14219674dcc7e3a1.mockapi.io"
}

# Timeout máximo (segundos) aplicado às requisições de saída aprovadas.
OUTBOUND_TIMEOUT_SECONDS = 5.0


# ---------------------------------------------------------------------------
# Resultado da validação
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Resultado da passagem de uma URL pelas três camadas."""

    allowed: bool
    # Camada que decidiu (1, 2 ou 3). Em caso de aprovação total, layer = None.
    layer: int | None = None
    layer_name: str | None = None
    reason: str = ""
    # Informações auxiliares coletadas durante a validação (host, IPs, etc.).
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "blocked_by_layer": self.layer,
            "layer_name": self.layer_name,
            "reason": self.reason,
            "details": self.details,
        }


def _block(layer: int, layer_name: str, reason: str, **details) -> ValidationResult:
    return ValidationResult(
        allowed=False,
        layer=layer,
        layer_name=layer_name,
        reason=reason,
        details=details,
    )


# ---------------------------------------------------------------------------
# Camada 2 - ranges de IP bloqueados
# ---------------------------------------------------------------------------

# Redes cuja simples menção já configura acesso a recursos internos/privilegiados.
BLOCKED_NETWORKS = [
    # Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    # RFC 1918 - redes privadas
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Link-local / serviços de metadados de nuvem (169.254.169.254)
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    # IPv6 Unique Local Addresses (RFC 4193)
    ipaddress.ip_network("fc00::/7"),
    # Endereço não especificado / broadcast
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::/128"),
    # Carrier-grade NAT (RFC 6598)
    ipaddress.ip_network("100.64.0.0/10"),
]


def _ip_is_blocked(ip: ipaddress._BaseAddress) -> tuple[bool, str]:
    """Retorna (bloqueado, motivo) para um IP já resolvido."""
    # Cobre casos não enumerados explicitamente (multicast, reservados, etc.).
    if not ip.is_global:
        # Detalha o motivo mais específico possível.
        if ip.is_loopback:
            return True, f"IP de loopback ({ip})"
        if ip.is_link_local:
            return True, f"IP link-local / metadados de nuvem ({ip})"
        if ip.is_private:
            return True, f"IP de rede privada RFC 1918 ({ip})"
        if ip.is_reserved:
            return True, f"IP reservado ({ip})"
        if ip.is_unspecified:
            return True, f"IP não especificado ({ip})"
        return True, f"IP não roteável publicamente ({ip})"

    for net in BLOCKED_NETWORKS:
        if ip in net:
            return True, f"IP dentro de range bloqueado {net} ({ip})"

    return False, ""


# ---------------------------------------------------------------------------
# Camada 1 - esquema e estrutura da URL
# ---------------------------------------------------------------------------


def _layer1_scheme_and_structure(raw_url: str) -> ValidationResult:
    name = "Camada 1 - Esquema e estrutura"
    url = (raw_url or "").strip()

    if not url:
        return _block(1, name, "URL vazia.")

    # Caracteres de controle (ex.: %0d%0a já decodificado, \n, \t) - CRLF/ofuscação.
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        return _block(1, name, "URL contém caracteres de controle.")

    try:
        parts = urlsplit(url)
    except ValueError as exc:
        return _block(1, name, f"URL malformada: {exc}")

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return _block(
            1,
            name,
            f"Esquema '{scheme or '(vazio)'}' não permitido. "
            f"Apenas {sorted(ALLOWED_SCHEMES)} são aceitos "
            f"(bloqueia file://, gopher://, dict://, ftp://, etc.).",
            scheme=scheme,
        )

    # Credenciais embutidas (http://usuario@169.254.169.254/) - vetor de ofuscação.
    if parts.username or parts.password or "@" in parts.netloc:
        return _block(
            1,
            name,
            "URL contém credenciais embutidas (userinfo '@'), padrão usado "
            "para ofuscar o host real.",
        )

    host = parts.hostname
    if not host:
        return _block(1, name, "URL sem hostname.")

    # Detecta IPs ofuscados em notação decimal/hexadecimal/octal.
    # Ex.: http://2130706433/  ==  http://127.0.0.1/
    obfuscated = _detect_obfuscated_ip(host)
    if obfuscated:
        return _block(
            1,
            name,
            f"Host usa notação numérica ofuscada de IP ({host} → {obfuscated}). "
            "Rejeitado por evasão.",
            host=host,
            decoded_ip=str(obfuscated),
        )

    return ValidationResult(
        allowed=True,
        details={"scheme": scheme, "host": host, "port": parts.port},
    )


def _detect_obfuscated_ip(host: str) -> ipaddress._BaseAddress | None:
    """Detecta IPv4 escrito como decimal/hex/octal único (evasão de filtros)."""
    h = host.strip()

    # Já é um IP em notação pontuada normal → não é "ofuscado", trata na Camada 2.
    try:
        ipaddress.ip_address(h)
        return None
    except ValueError:
        pass

    candidate: int | None = None
    try:
        if h.lower().startswith("0x"):  # hexadecimal: 0x7f000001
            candidate = int(h, 16)
        elif h.startswith("0") and h.isdigit() and h != "0":  # octal: 017700000001
            candidate = int(h, 8)
        elif h.isdigit():  # decimal único: 2130706433
            candidate = int(h)
    except ValueError:
        return None

    if candidate is None:
        return None

    try:
        return ipaddress.ip_address(candidate)  # inteiro → IPv4/IPv6
    except (ValueError, ipaddress.AddressValueError):
        return None


# ---------------------------------------------------------------------------
# Camada 2 - resolução DNS e verificação de IP
# ---------------------------------------------------------------------------


def _resolve_all_ips(host: str) -> list[ipaddress._BaseAddress]:
    """Resolve todos os IPs (v4 e v6) de um host via getaddrinfo."""
    ips: list[ipaddress._BaseAddress] = []

    # Se já for um literal de IP, não há DNS a resolver.
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass

    infos = socket.getaddrinfo(host, None)  # pode lançar socket.gaierror
    seen = set()
    for family, _type, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        if ip_str in seen:
            continue
        seen.add(ip_str)
        try:
            ips.append(ipaddress.ip_address(ip_str))
        except ValueError:
            continue
    return ips


def _layer2_dns_and_ip(host: str) -> ValidationResult:
    name = "Camada 2 - Resolução DNS e IP de destino"
    try:
        ips = _resolve_all_ips(host)
    except socket.gaierror as exc:
        return _block(
            2, name, f"Falha ao resolver DNS de '{host}': {exc}.", host=host
        )

    if not ips:
        return _block(2, name, f"Host '{host}' não resolveu para nenhum IP.", host=host)

    resolved = [str(ip) for ip in ips]

    # TODOS os IPs devem ser públicos - se qualquer um for interno, bloqueia
    # (defesa contra DNS rebinding e registros com múltiplos A).
    for ip in ips:
        blocked, why = _ip_is_blocked(ip)
        if blocked:
            return _block(
                2,
                name,
                f"Destino bloqueado: {why}. "
                "Impede acesso a loopback, redes privadas e metadados de nuvem.",
                host=host,
                resolved_ips=resolved,
            )

    return ValidationResult(
        allowed=True,
        details={"host": host, "resolved_ips": resolved},
    )


# ---------------------------------------------------------------------------
# Camada 3 - allowlist de domínios
# ---------------------------------------------------------------------------


def _layer3_allowlist(host: str, allowlist: set[str]) -> ValidationResult:
    name = "Camada 3 - Allowlist de domínios"
    h = host.lower().rstrip(".")

    # Match exato ou subdomínio de um domínio autorizado.
    for allowed in allowlist:
        a = allowed.lower()
        if h == a or h.endswith("." + a):
            return ValidationResult(allowed=True, details={"matched_allow": allowed})

    return _block(
        3,
        name,
        f"Domínio '{host}' não está na allowlist de parceiros autorizados. "
        "Paradigma de negação por padrão: só destinos explicitamente permitidos "
        "podem receber webhooks.",
        host=host,
        allowlist=sorted(allowlist),
    )


# ---------------------------------------------------------------------------
# Orquestração das três camadas
# ---------------------------------------------------------------------------


def validate_url(raw_url: str, allowlist: set[str] | None = None) -> ValidationResult:
    """
    Submete a URL às três camadas EM SÉRIE. Retorna no primeiro bloqueio;
    só aprova se passar por todas. Nenhuma requisição de rede de saída é feita
    aqui - apenas resolução DNS (necessária para a Camada 2).
    """
    allow = allowlist if allowlist is not None else DEFAULT_ALLOWLIST

    # Camada 1
    r1 = _layer1_scheme_and_structure(raw_url)
    if not r1.allowed:
        return r1
    host = r1.details["host"]

    # Camada 2
    r2 = _layer2_dns_and_ip(host)
    if not r2.allowed:
        return r2

    # Camada 3
    r3 = _layer3_allowlist(host, allow)
    if not r3.allowed:
        return r3

    # Aprovado em todas as camadas.
    return ValidationResult(
        allowed=True,
        reason="URL aprovada nas três camadas de validação.",
        details={
            "scheme": r1.details["scheme"],
            "host": host,
            "resolved_ips": r2.details.get("resolved_ips"),
            "matched_allow": r3.details.get("matched_allow"),
        },
    )
