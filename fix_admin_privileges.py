
#!/usr/bin/env python3
"""
Script para corrigir privilégios de admin incorretos no banco de dados.
Execute este script uma vez para limpar todos os usuários com privilégios incorretos.
"""

from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import User

def fix_admin_privileges():
    """Corrige privilégios de admin incorretos no banco de dados"""
    
    # Lista de emails autorizados como admin
    AUTHORIZED_ADMIN_EMAILS = [
        "admin@fovdark.com",
        "lsalles102@gmail.com"
    ]
    
    # Converter para lowercase para comparação
    authorized_emails_lower = [email.lower() for email in AUTHORIZED_ADMIN_EMAILS]
    
    db = SessionLocal()
    try:
        # Buscar todos os usuários
        all_users = db.query(User).all()
        
        fixed_count = 0
        
        for user in all_users:
            user_email_lower = user.email.lower().strip()
            is_authorized = user_email_lower in authorized_emails_lower
            
            if is_authorized and not user.is_admin:
                # Usuário autorizado que deveria ser admin
                user.is_admin = True
                print(f"✅ {user.email} promovido a admin")
                fixed_count += 1
                
            elif not is_authorized and user.is_admin:
                # Usuário não autorizado que era admin incorretamente
                user.is_admin = False
                print(f"❌ Privilégios de admin removidos de {user.email}")
                fixed_count += 1
                
            else:
                print(f"✓ {user.email} - status correto (admin: {user.is_admin})")
        
        if fixed_count > 0:
            db.commit()
            print(f"\n🔧 {fixed_count} usuários corrigidos com sucesso!")
        else:
            print("\n✅ Todos os usuários já possuem privilégios corretos!")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir privilégios: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Iniciando correção de privilégios de admin...")
    print("📋 Emails autorizados como admin:")
    print("   - admin@fovdark.com")
    print("   - lsalles102@gmail.com")
    print()
    
    fix_admin_privileges()
    
    print("\n✅ Correção concluída!")
