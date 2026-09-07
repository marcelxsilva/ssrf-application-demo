# tools/ - scripts de exploração SSRF

Scripts em Python que mostram, passo a passo, como o atacante explora o SSRF do
FinanceHub e chega aos dados de outras contas. Cada script é independente: tem
seu próprio bloco de configuração no topo e roda sozinho.

Uso apenas educacional, contra o ambiente local deste projeto. Dados fictícios.

## A ideia

O atacante não tem acesso à rede interna. A ferramenta dele é a própria
vulnerabilidade: o endpoint `/vulnerable/webhook/test` faz o servidor buscar
qualquer URL. Ou seja, o servidor é usado como intermediário.

Por isso cada script tem dois endereços no topo:

- `APP_URL`: onde o FinanceHub roda (o alvo). Ex.: `http://localhost:8000`.
- `INTERNAL_API` (ou `--subnet` no scanner): o que o servidor deve alcançar por
  dentro, em nome do atacante.

## Preparar

Aplicação no ar (`docker compose up`) e o ambiente criado com uv:

```bash
cd tools
uv sync
uv run network_scanner.py
```

Se a aplicação não estiver em `localhost:8000`, ajuste `APP_URL` no topo do
script.

## As etapas

**1. Descobrir a rede interna** (`network_scanner.py`)

O atacante não sabe quais IPs existem, então varre as faixas privadas mais comuns
e usa a resposta como pista: quem responde (ou recusa rápido) está vivo. A saída
lista só as portas abertas, no formato `ip:porta`.

```bash
uv run network_scanner.py --subnet 10.5.0.0/24
# 10.5.0.15:8080
```

**2. Identificar o serviço e as rotas** (`service_prober.py`)

Sonda caminhos comuns no host aberto e, principalmente, lê o schema
`/openapi.json` que a API expõe. É por ele que o atacante descobre a rota
`/admin/accounts/{username}/transactions`, sem precisar adivinhar.

```bash
uv run service_prober.py
# 200  /admin/accounts
# GET   /admin/accounts/{username}/transactions
```

**3. Enumerar as contas** (`account_enumerator.py`)

A API interna expõe `/admin/accounts` sem autenticação. Via SSRF, lista todos os
usuários.

```bash
uv run account_enumerator.py
# joao, maria, ana
```

**4. Exfiltrar os extratos** (`transaction_exfiltrator.py`)

Para cada conta, busca o extrato completo e salva em `loot.json`.

```bash
uv run transaction_exfiltrator.py
```

**Tudo de uma vez** (`chain_attack.py`)

```bash
uv run chain_attack.py
```

## Ajustar o alvo

Para apontar para outra máquina, mude `APP_URL` no topo do script. Os endereços
internos (`INTERNAL_API`, `--subnet`) só mudam se você alterar a rede do
`docker-compose` (hoje `10.5.0.0/24`).
