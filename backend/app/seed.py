"""Cria as tabelas e popula usuários + transações (idempotente)."""

from datetime import date

from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import Transaction, User

# senha padrão de todos os usuários da demo
DEFAULT_PASSWORD = "senha123"

USERS = [
    {
        "username": "joao", "full_name": "João Pereira", "account_number": "0001-01",
        "transactions": [
            ("2026-08-02", "credito", "Depósito", 1200.00),
            ("2026-08-10", "transferencia", "PIX recebido de Maria", 150.00),
            ("2026-08-11", "debito", "Assinatura streaming", -39.90),
        ],
    },
    {
        "username": "maria", "full_name": "Maria Souza", "account_number": "0002-01",
        "transactions": [
            ("2026-08-01", "credito", "Salário", 8500.00),
            ("2026-08-03", "debito", "Aluguel", -2200.00),
            ("2026-08-07", "debito", "Mercado", -643.19),
            ("2026-08-10", "transferencia", "PIX enviado para João", -150.00),
            ("2026-08-12", "debito", "Farmácia", -87.40),
        ],
    },
    {
        "username": "ana", "full_name": "Ana Lima", "account_number": "0003-01",
        "transactions": [
            ("2026-08-05", "credito", "Freelance design", 3200.00),
            ("2026-08-09", "debito", "Restaurante", -156.00),
        ],
    },
]


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("[seed] banco já populado - nada a fazer.")
            return
        for u in USERS:
            user = User(
                username=u["username"],
                full_name=u["full_name"],
                account_number=u["account_number"],
                password_hash=hash_password(DEFAULT_PASSWORD),
            )
            for d, kind, desc, amount in u["transactions"]:
                user.transactions.append(
                    Transaction(
                        tx_date=date.fromisoformat(d),
                        kind=kind,
                        description=desc,
                        amount=amount,
                    )
                )
            db.add(user)
        db.commit()
        print(f"[seed] {len(USERS)} usuários criados (senha padrão: {DEFAULT_PASSWORD}).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
