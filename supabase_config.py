# Configuração para usar Supabase em vez do PostgreSQL local
# Substitua as variáveis no arquivo database.py quando for usar Supabase

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL do Supabase PostgreSQL
# Formato: postgresql://postgres:[SUA_SENHA]@db.[SEU_PROJETO].supabase.co:5432/postgres
SUPABASE_DATABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL", 
    "postgresql://postgres:[SUA_SENHA]@db.[SEU_PROJETO].supabase.co:5432/postgres"
)

# Configurar engine do SQLAlchemy para Supabase
engine = create_engine(
    SUPABASE_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Definir como True para debug SQL
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

# Instruções para configurar no Supabase:
"""
1. Acesse seu projeto no Supabase
2. Vá em Settings > Database
3. Copie a Connection string
4. Execute o arquivo supabase_schema.sql no SQL Editor
5. Configure a variável SUPABASE_DATABASE_URL no seu ambiente
6. Substitua o conteúdo de database.py por este arquivo
"""