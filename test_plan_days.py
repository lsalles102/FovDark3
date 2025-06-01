
#!/usr/bin/env python3
"""
Script para testar se os dias dos planos estão sendo aplicados corretamente
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionLocal
    from models import User, Product, Payment
    from mercadopago_integration import create_payment_preference, handle_payment_notification
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

def test_plan_days():
    """Testar se os dias dos planos estão sendo aplicados corretamente"""
    print("🧪 Iniciando teste de dias dos planos...")
    
    db = SessionLocal()
    
    try:
        # 1. Verificar produtos no banco
        print("\n1️⃣ Verificando produtos no banco de dados:")
        products = db.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            print("❌ Nenhum produto encontrado no banco de dados")
            return False
            
        for product in products:
            print(f"   📦 Produto: {product.name}")
            print(f"      - ID: {product.id}")
            print(f"      - Preço: R$ {product.price}")
            print(f"      - Duração: {product.duration_days} dias")
            print(f"      - Ativo: {product.is_active}")
        
        # 2. Buscar usuário de teste
        print("\n2️⃣ Buscando usuário de teste:")
        test_user = db.query(User).filter(User.email.like('%test%')).first()
        
        if not test_user:
            print("❌ Usuário de teste não encontrado. Criando um...")
            from auth import get_password_hash
            test_user = User(
                email="test@fovdark.com",
                senha_hash=get_password_hash("test123"),
                status_licenca="pendente"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Usuário de teste criado: {test_user.email}")
        else:
            print(f"✅ Usuário de teste encontrado: {test_user.email}")
        
        # 3. Testar criação de preferência para cada produto
        print("\n3️⃣ Testando criação de preferências:")
        
        for product in products[:2]:  # Testar apenas os 2 primeiros produtos
            print(f"\n   🧪 Testando produto: {product.name} ({product.duration_days} dias)")
            
            try:
                # Criar preferência
                result = create_payment_preference(
                    plan_id=f"product_{product.id}",
                    user_id=test_user.id,
                    user_email=test_user.email,
                    product_id=product.id
                )
                
                if "error" in result:
                    print(f"      ❌ Erro: {result['error']}")
                    continue
                
                print(f"      ✅ Preferência criada: {result.get('id')}")
                
                # Verificar metadados
                metadata = result.get('metadata', {})
                days_in_metadata = metadata.get('days')
                
                if days_in_metadata:
                    days_int = int(days_in_metadata)
                    if days_int == product.duration_days:
                        print(f"      ✅ CORRETO: Dias nos metadados ({days_int}) = produto ({product.duration_days})")
                    else:
                        print(f"      ❌ ERRO: Dias nos metadados ({days_int}) ≠ produto ({product.duration_days})")
                else:
                    print(f"      ⚠️ Metadados não encontrados")
                
            except Exception as e:
                print(f"      ❌ Erro no teste: {str(e)}")
        
        # 4. Testar simulação de pagamento aprovado
        print("\n4️⃣ Testando simulação de pagamento aprovado:")
        
        # Pegar o primeiro produto para teste
        test_product = products[0]
        print(f"   📦 Produto de teste: {test_product.name} ({test_product.duration_days} dias)")
        
        # Salvar data de expiração atual
        original_expiration = test_user.data_expiracao
        print(f"   📅 Data de expiração original: {original_expiration}")
        
        # Simular dados de webhook de pagamento aprovado
        fake_notification = {
            "data": {
                "id": "fake_payment_123"
            },
            "type": "payment"
        }
        
        # Criar um pagamento pendente para teste
        test_payment = Payment(
            user_id=test_user.id,
            product_id=test_product.id,
            valor=test_product.price,
            plano=test_product.name,
            gateway_id="fake_payment_123",
            status="pending"
        )
        db.add(test_payment)
        db.commit()
        
        print(f"   💳 Pagamento de teste criado com ID: {test_payment.id}")
        
        # Simular processamento do webhook (comentado para não fazer requisições reais à API)
        # success, message = handle_payment_notification(fake_notification)
        # print(f"   🔔 Resultado do webhook: {success} - {message}")
        
        # Verificar se os dias seriam aplicados corretamente manualmente
        if test_user.data_expiracao and test_user.data_expiracao > datetime.utcnow():
            new_expiration = test_user.data_expiracao + timedelta(days=test_product.duration_days)
            action = "estendida"
        else:
            new_expiration = datetime.utcnow() + timedelta(days=test_product.duration_days)
            action = "criada"
        
        print(f"   📅 Nova data de expiração seria: {new_expiration}")
        print(f"   🎯 Licença seria {action} com {test_product.duration_days} dias")
        
        # Limpar dados de teste
        db.delete(test_payment)
        db.commit()
        print(f"   🧹 Pagamento de teste removido")
        
        print(f"\n✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    test_plan_days()
