
#!/usr/bin/env python3
"""
Script para corrigir status das licenças baseado na data de expiração
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionLocal
    from models import User
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que os arquivos database.py e models.py existem e estão corretos.")
    sys.exit(1)

def fix_license_status():
    """Corrigir status das licenças baseado na data de expiração"""
    print("🔧 Iniciando correção de status das licenças...")
    
    try:
        db = SessionLocal()
        print("✅ Conexão com banco de dados estabelecida")
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco de dados: {e}")
        return False
    
    try:
        # Buscar todos os usuários
        users = db.query(User).all()
        now = datetime.utcnow()
        updated_count = 0
        
        print(f"🔍 Verificando {len(users)} usuários...")
        print(f"📅 Data/hora atual: {now}")
        print("-" * 60)
        
        for user in users:
            old_status = user.status_licenca
            print(f"\n👤 Usuário: {user.email}")
            print(f"   Status atual: {old_status}")
            print(f"   Data expiração: {user.data_expiracao}")
            
            if not user.data_expiracao:
                # Sem data de expiração - manter como pendente ou sem licença
                if user.status_licenca not in ["pendente", "sem_licenca"]:
                    user.status_licenca = "sem_licenca"
                    updated_count += 1
                    print(f"   ✅ Alterado: {old_status} → sem_licenca (sem data de expiração)")
                else:
                    print(f"   ✓ Status correto: {old_status}")
                    
            elif user.data_expiracao > now:
                # Data de expiração válida - licença ativa
                days_remaining = (user.data_expiracao - now).days
                if user.status_licenca != "ativa":
                    user.status_licenca = "ativa"
                    updated_count += 1
                    print(f"   ✅ Alterado: {old_status} → ativa (expira em {days_remaining} dias)")
                else:
                    print(f"   ✓ Status correto: ativa (expira em {days_remaining} dias)")
                    
            else:
                # Data de expiração passou - licença expirada
                days_expired = (now - user.data_expiracao).days
                if user.status_licenca != "expirada":
                    user.status_licenca = "expirada"
                    updated_count += 1
                    print(f"   ✅ Alterado: {old_status} → expirada (há {days_expired} dias)")
                else:
                    print(f"   ✓ Status correto: expirada (há {days_expired} dias)")
        
        # Salvar alterações
        if updated_count > 0:
            db.commit()
            print(f"\n💾 Alterações salvas no banco de dados")
        else:
            print(f"\n📝 Nenhuma alteração necessária")
            
        print(f"\n🎯 Processo concluído! {updated_count} usuários tiveram o status corrigido.")
        
        # Mostrar resumo
        print("\n" + "="*60)
        print("📊 RESUMO ATUAL:")
        
        active_count = db.query(User).filter(User.status_licenca == "ativa").count()
        expired_count = db.query(User).filter(User.status_licenca == "expirada").count()
        pending_count = db.query(User).filter(User.status_licenca == "pendente").count()
        no_license_count = db.query(User).filter(User.status_licenca == "sem_licenca").count()
        
        print(f"   🟢 Licenças Ativas: {active_count}")
        print(f"   🔴 Licenças Expiradas: {expired_count}")
        print(f"   🟡 Pagamentos Pendentes: {pending_count}")
        print(f"   ⚪ Sem Licença: {no_license_count}")
        print("="*60)
        
        # Mostrar detalhes dos usuários com licenças ativas
        if active_count > 0:
            print(f"\n📋 USUÁRIOS COM LICENÇA ATIVA:")
            active_users = db.query(User).filter(User.status_licenca == "ativa").all()
            for user in active_users:
                if user.data_expiracao:
                    days_remaining = (user.data_expiracao - now).days
                    print(f"   • {user.email} - expira em {days_remaining} dias ({user.data_expiracao.strftime('%d/%m/%Y %H:%M')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
        
    finally:
        db.close()
        print("\n🔒 Conexão com banco de dados fechada")

if __name__ == "__main__":
    print("🚀 Script de Correção de Status das Licenças")
    print("="*60)
    
    success = fix_license_status()
    
    if success:
        print("\n✅ Script executado com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Script falhou durante a execução!")
        sys.exit(1)
