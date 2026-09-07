# FinanceHub - Demo de SSRF

Aplicação financeira fictícia usada para demonstrar a vulnerabilidade de SSRF
(Server-Side Request Forgery) e a correção dela. Tem login real, banco de dados
e serviços internos isolados em rede.

A mesma aplicação é servida em duas versões, separadas por rota:

- `/vulnerable` : sem validação de URL no webhook. O SSRF é explorável.
- `/secure` : mesma aplicação com um validador de URL em 3 camadas.

O cenário: o usuário João, logado, usa o webhook para fazer o servidor acessar
uma API interna sem autenticação e ler o extrato da conta da Maria, algo que o
navegador dele não alcança diretamente.

## Como rodar

Precisa de Docker.

```bash
cd ssrf-demo
docker compose up --build
```

- Aplicação: http://localhost:5180
- Versão vulnerável: http://localhost:5180/vulnerable
- Versão segura: http://localhost:5180/secure
- Contas de teste: `joao`, `maria`, `ana`, todas com a senha `senha123`

Para parar: `docker compose down` (ou `down -v` para apagar o banco).

## Arquitetura

Docker Compose com duas redes:

- Rede de borda: acessível pelo navegador. Ficam o `frontend` (React) e o
  `backend` (FastAPI).
- Rede interna `finnet` (`10.5.0.0/24`, `internal: true`): sem internet e
  inacessível a partir do host. Ficam o banco `db` (PostgreSQL) e a
  `internal-api` (API administrativa sem autenticação).

O `backend` participa das duas redes. É essa ponte que o SSRF explora: o
navegador não alcança `10.5.0.0/24`, mas consegue fazer o backend alcançar.

## O webhook de teste (versão segura)

Na versão segura, os destinos permitidos ficam numa allowlist. Para ver as
transações reais chegando de verdade num webhook externo, use este endereço:

```
https://686c60dc14219674dcc7e3a1.mockapi.io/api/test
```

Basta abrir essa URL no navegador para ver a lista do que já foi recebido. No
FinanceHub, entre em `/secure`, faça login, vá em Webhooks, cole essa URL e
clique em Salvar. A cada nova transação (o servidor gera uma por usuário a cada
2 minutos), o backend entrega a notificação nesse endereço e o mockapi passa a
listá-la.

## Roteiro da demonstração

1. Abra `/vulnerable` e entre como `joao`. Você vê só as suas movimentações.
2. Vá em Webhooks e cole `http://10.5.0.15:8080/admin/accounts/maria/transactions`.
3. Clique em Testar. O servidor busca essa URL interna e devolve o extrato da
   Maria. É o SSRF.
4. Abra `/secure`, entre de novo e repita a mesma URL. O validador bloqueia na
   camada 2 (IP privado).
5. Ainda em `/secure`, salve o webhook do mockapi acima e acompanhe as entregas.

Para reproduzir a descoberta automatizada do ataque (varredura da rede,
enumeração de contas e exfiltração), veja a pasta `tools/`.

## Estrutura

```
ssrf-demo/
  frontend/       React + Vite (login, dashboard, webhooks)
  backend/        FastAPI + SQLAlchemy (auth, transações, rotas /vulnerable e /secure)
  internal-api/   API interna sem autenticação (alvo do SSRF)
  tools/          scripts de exploração (ver tools/README.md)
  docker-compose.yml
```

Todos os dados (contas, transações) são fictícios e o projeto é apenas para fins
educacionais.
