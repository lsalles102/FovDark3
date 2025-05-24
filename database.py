import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do banco de dados PostgreSQL com fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.zqytkijzrtcripepqcbg:Capitulo4v3@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")

if not DATABASE_URL:
    # Fallback para desenvolvimento - SQLite
    DATABASE_URL = "sqlite:///./darkfov.db"
    print("⚠️  Usando SQLite para desenvolvimento local")
else:
    # Corrigir URL do PostgreSQL para Railway se necessário
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("✅ Conectando ao PostgreSQL em produção")

# Configurar engine do SQLAlchemy
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
            "application_name": "DarkFov"
        },
        echo=False
    )

# Configurar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()


# Dependency para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
