"""Conexão com o PostgreSQL (SQLAlchemy) compartilhada pela aplicação."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://financehub:financehub@db:5432/financehub"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Dependency do FastAPI: fornece uma sessão por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
