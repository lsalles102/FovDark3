
#!/usr/bin/env python3

import sys
from database import SessionLocal, engine, Base
from models import User
from auth import get_password_hash, verify_password

def test_database():
    """Testar conexão com banco e listar usuários"""
    print("=== TESTE DE BANCO DE DADOS ===")
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas/verificadas")
        
        db = SessionLocal()
        
        # Listar todos os usuários
        users = db.query(User).all()
        print(f"\n📊 Total de usuários no banco: {len(users)}")
        
        if users:
            print("\n👥 Usuários encontrados:")
            for user in users:
                print(f"  - ID: {user.id}")
                print(f"    Email: {user.email}")
                print(f"    Admin: {user.is_admin}")
                print(f"    Criado em: {user.created_at}")
                print(f"    Expira em: {user.data_expiracao}")
                print("---")
        else:
            print("⚠️  Nenhum usuário encontrado no banco")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao acessar banco: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_admin_user():
    """Criar usuário administrador"""
    print("\n=== CRIANDO USUÁRIO ADMIN ===")
    
    admin_email = "lsalles102@gmail.com"
    admin_password = "admin123"  # Mude esta senha!
    
    try:
        db = SessionLocal()
        
        # Verificar se admin já existe
        existing_admin = db.query(User).filter(User.email.ilike(admin_email)).first()
        if existing_admin:
            print(f"⚠️  Admin já existe: {admin_email}")
            print(f"   Status admin: {existing_admin.is_admin}")
            
            # Garantir que seja admin
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                db.commit()
                print("✅ Status de admin atualizado")
            
            db.close()
            return existing_admin
        
        # Criar novo admin
        hashed_password = get_password_hash(admin_password)
        
        new_admin = User(
            email=admin_email,
            senha_hash=hashed_password,
            is_admin=True,
            data_expiracao=None
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        print(f"✅ Admin criado com sucesso!")
        print(f"   Email: {admin_email}")
        print(f"   Senha: {admin_password}")
        print(f"   ID: {new_admin.id}")
        
        db.close()
        return new_admin
        
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_login():
    """Testar login do usuário admin"""
    print("\n=== TESTE DE LOGIN ===")
    
    admin_email = "lsalles102@gmail.com"
    admin_password = "admin123"
    
    try:
        db = SessionLocal()
        
        # Buscar usuário
        user = db.query(User).filter(User.email.ilike(admin_email)).first()
        if not user:
            print(f"❌ Usuário não encontrado: {admin_email}")
            return False
        
        print(f"✅ Usuário encontrado: {user.email}")
        
        # Testar senha
        password_valid = verify_password(admin_password, user.senha_hash)
        print(f"🔐 Teste de senha: {'✅ VÁLIDA' if password_valid else '❌ INVÁLIDA'}")
        
        if password_valid:
            print(f"🎉 Login funcionando para: {admin_email}")
            return True
        else:
            print(f"❌ Falha no login para: {admin_email}")
            return False
        
        db.close()
        
    except Exception as e:
        print(f"❌ Erro no teste de login: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Iniciando diagnóstico do sistema de login...")
    
    # Testar banco
    if not test_database():
        print("❌ Falha no teste do banco de dados")
        return
    
    # Criar admin se necessário
    admin = create_admin_user()
    if not admin:
        print("❌ Falha ao criar/verificar admin")
        return
    
    # Testar login
    if test_login():
        print("\n🎉 SISTEMA DE LOGIN FUNCIONANDO!")
        print("\n📋 Credenciais de teste:")
        print("   Email: lsalles102@gmail.com")
        print("   Senha: admin123")
        print("\n⚠️  IMPORTANTE: Mude a senha após o primeiro login!")
    else:
        print("\n❌ SISTEMA DE LOGIN COM PROBLEMAS")

if __name__ == "__main__":
    main()
