
from datetime import datetime
from database import get_db, SessionLocal
from models import User

def fix_license_status():
    """Corrigir status das licenças baseado na data de expiração"""
    db = SessionLocal()
    
    try:
        # Buscar todos os usuários
        users = db.query(User).all()
        now = datetime.utcnow()
        updated_count = 0
        
        print(f"🔍 Verificando {len(users)} usuários...")
        
        for user in users:
            old_status = user.status_licenca
            
            if not user.data_expiracao:
                # Sem data de expiração - manter como pendente ou sem licença
                if user.status_licenca not in ["pendente", "sem_licenca"]:
                    user.status_licenca = "sem_licenca"
                    updated_count += 1
                    print(f"✅ {user.email}: {old_status} → sem_licenca (sem data de expiração)")
            elif user.data_expiracao > now:
                # Data de expiração válida - licença ativa
                if user.status_licenca != "ativa":
                    user.status_licenca = "ativa"
                    updated_count += 1
                    days_remaining = (user.data_expiracao - now).days
                    print(f"✅ {user.email}: {old_status} → ativa (expira em {days_remaining} dias)")
            else:
                # Data de expiração passou - licença expirada
                if user.status_licenca != "expirada":
                    user.status_licenca = "expirada"
                    updated_count += 1
                    days_expired = (now - user.data_expiracao).days
                    print(f"✅ {user.email}: {old_status} → expirada (há {days_expired} dias)")
        
        # Salvar alterações
        db.commit()
        print(f"\n🎯 Processo concluído! {updated_count} usuários tiveram o status corrigido.")
        
        # Mostrar resumo
        active_count = db.query(User).filter(User.status_licenca == "ativa").count()
        expired_count = db.query(User).filter(User.status_licenca == "expirada").count()
        pending_count = db.query(User).filter(User.status_licenca == "pendente").count()
        no_license_count = db.query(User).filter(User.status_licenca == "sem_licenca").count()
        
        print(f"\n📊 Resumo atual:")
        print(f"   🟢 Ativas: {active_count}")
        print(f"   🔴 Expiradas: {expired_count}")
        print(f"   🟡 Pendentes: {pending_count}")
        print(f"   ⚪ Sem licença: {no_license_count}")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir status das licenças: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_license_status()
