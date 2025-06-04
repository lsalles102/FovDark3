#!/usr/bin/env python3
"""
Script de inicialização do DarkFov para Railway
Aguarda o banco estar disponível antes de iniciar a aplicação
"""
import os
import time
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def wait_for_database(max_retries=30, delay=2):
    """Aguarda o banco de dados ficar disponível"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("✅ Modo desenvolvimento - usando SQLite")
        return True

    # Corrigir URL se necessário
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"🔄 Aguardando banco de dados ficar disponível...")

    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Banco de dados conectado com sucesso!")
            return True
        except OperationalError as e:
            print(f"⏳ Tentativa {attempt + 1}/{max_retries} - Aguardando banco... ({delay}s)")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                print(f"❌ Falha ao conectar após {max_retries} tentativas: {e}")
                return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False

    return False

def create_admin_user():
    """Cria usuário admin se não existir"""
    try:
        from database import SessionLocal
        from models import User
        from auth import get_password_hash

        db = SessionLocal()
        admin = db.query(User).filter(User.email == "admin@darkfov.com").first()

        if not admin:
            admin_user = User(
                email="admin@darkfov.com",
                senha_hash=get_password_hash("secret"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Usuário admin criado: admin@darkfov.com / secret")
        else:
            print("✅ Usuário admin já existe")

        db.close()
    except Exception as e:
        print(f"⚠️  Erro ao criar admin: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando FovDark...")

    # Aguardar banco de dados
    if not wait_for_database():
        print("❌ Falha ao conectar com o banco - encerrando")
        sys.exit(1)

    # Criar tabelas
    try:
        from database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas do banco criadas/verificadas")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        sys.exit(1)

    # Criar usuário admin
    create_admin_user()

    # Iniciar aplicação
    print("🎯 Iniciando servidor FovDark...")

    # Importar e executar
    import uvicorn
    from main import app

    try:
        port = int(os.environ.get("PORT", 5000))
        print(f"🚀 Iniciando servidor na porta {port}...")
        print(f"🌐 Acesse: http://0.0.0.0:{port}")

        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        raise