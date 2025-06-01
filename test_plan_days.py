
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
#!/usr/bin/env python3

import os
from datetime import datetime
from database import SessionLocal
from models import Product, User, Payment
from mercadopago_integration import create_payment_preference, handle_payment_notification

def test_products_days():
    """Testar se os dias dos produtos estão sendo aplicados corretamente"""
    db = SessionLocal()
    
    try:
        print("🔍 VERIFICAÇÃO DOS DIAS DOS PRODUTOS")
        print("=" * 50)
        
        # Buscar todos os produtos ativos
        products = db.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            print("❌ Nenhum produto encontrado no banco")
            return
        
        print(f"📦 Encontrados {len(products)} produtos ativos:")
        print()
        
        for product in products:
            print(f"🎯 PRODUTO: {product.name}")
            print(f"   📅 Dias configurados: {product.duration_days}")
            print(f"   💰 Preço: R$ {product.price}")
            print(f"   🔗 ID: {product.id}")
            print()
        
        # Buscar um usuário de teste
        test_user = db.query(User).filter(User.email.like("%test%")).first()
        if not test_user:
            test_user = db.query(User).first()
        
        if not test_user:
            print("❌ Nenhum usuário encontrado para teste")
            return
        
        print(f"👤 Usuário de teste: {test_user.email}")
        print()
        
        # Testar criação de preferência para cada produto
        for product in products:
            print(f"🧪 TESTANDO PRODUTO: {product.name} ({product.duration_days} dias)")
            print("-" * 40)
            
            try:
                # Criar preferência de pagamento
                result = create_payment_preference(
                    plan_id=f"product_{product.id}",
                    user_id=test_user.id,
                    user_email=test_user.email,
                    product_id=product.id
                )
                
                if "error" in result:
                    print(f"❌ Erro ao criar preferência: {result['error']}")
                else:
                    print(f"✅ Preferência criada com sucesso")
                    print(f"   🔗 Preference ID: {result.get('id', 'N/A')}")
                    
                    # Verificar metadados
                    metadata = result.get('metadata', {})
                    if metadata:
                        days_in_metadata = metadata.get('days', 'N/A')
                        print(f"   📅 Dias nos metadados: {days_in_metadata}")
                        
                        if str(days_in_metadata) == str(product.duration_days):
                            print(f"   ✅ CORRETO: Dias nos metadados correspondem ao produto")
                        else:
                            print(f"   ❌ ERRO: Dias nos metadados ({days_in_metadata}) ≠ produto ({product.duration_days})")
                    else:
                        print(f"   ⚠️ Metadados não encontrados na resposta")
                
            except Exception as e:
                print(f"❌ Erro no teste: {str(e)}")
            
            print()
        
        # Verificar produtos com problemas
        print("🔍 VERIFICAÇÃO DE PRODUTOS PROBLEMÁTICOS")
        print("=" * 50)
        
        problematic_products = []
        for product in products:
            if product.duration_days <= 1:
                problematic_products.append(product)
        
        if problematic_products:
            print("⚠️ Produtos com apenas 1 dia ou menos:")
            for product in problematic_products:
                print(f"   - {product.name}: {product.duration_days} dias")
        else:
            print("✅ Todos os produtos têm duração válida (> 1 dia)")
        
        print()
        
        # Resumo final
        print("📊 RESUMO FINAL")
        print("=" * 50)
        for product in products:
            status = "✅ OK" if product.duration_days > 1 else "❌ PROBLEMA"
            print(f"{status} {product.name}: {product.duration_days} dias - R$ {product.price}")
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {str(e)}")
    finally:
        db.close()

def show_current_products():
    """Mostrar produtos atuais do banco"""
    db = SessionLocal()
    
    try:
        products = db.query(Product).all()
        
        print("📦 PRODUTOS NO BANCO DE DADOS")
        print("=" * 50)
        
        if not products:
            print("❌ Nenhum produto encontrado")
            return
        
        for product in products:
            status = "🟢 ATIVO" if product.is_active else "🔴 INATIVO"
            featured = "⭐ DESTAQUE" if product.is_featured else ""
            
            print(f"{status} {product.name} {featured}")
            print(f"   📅 Duração: {product.duration_days} dias")
            print(f"   💰 Preço: R$ {product.price}")
            print(f"   🆔 ID: {product.id}")
            print(f"   📝 Descrição: {product.description[:50]}..." if product.description else "   📝 Sem descrição")
            print()
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    finally:
        db.close()

def simulate_purchase_flow(product_id):
    """Simular fluxo completo de compra para testar dias"""
    db = SessionLocal()
    
    try:
        print(f"🛒 SIMULANDO COMPRA DO PRODUTO ID: {product_id}")
        print("=" * 50)
        
        # Buscar produto
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            print(f"❌ Produto {product_id} não encontrado")
            return
        
        print(f"📦 Produto: {product.name}")
        print(f"📅 Dias configurados: {product.duration_days}")
        print(f"💰 Preço: R$ {product.price}")
        
        # Buscar usuário de teste
        test_user = db.query(User).first()
        if not test_user:
            print("❌ Nenhum usuário encontrado")
            return
        
        print(f"👤 Usuário: {test_user.email}")
        print(f"📅 Data atual de expiração: {test_user.data_expiracao}")
        
        # Simular notificação de pagamento aprovado
        fake_notification_data = {
            "type": "payment",
            "data": {
                "id": "123456789"
            }
        }
        
        # Criar pagamento pendente primeiro
        from mercadopago_integration import create_payment_preference
        
        preference_result = create_payment_preference(
            plan_id=f"product_{product.id}",
            user_id=test_user.id,
            user_email=test_user.email,
            product_id=product.id
        )
        
        if "error" in preference_result:
            print(f"❌ Erro na criação da preferência: {preference_result['error']}")
            return
            
        print(f"✅ Preferência criada: {preference_result.get('id')}")
        
        # Verificar se os dias estão corretos nos metadados
        metadata = preference_result.get('metadata', {})
        metadata_days = metadata.get('days', 0)
        
        print(f"📊 VERIFICAÇÃO DE CONSISTÊNCIA:")
        print(f"   Dias no produto: {product.duration_days}")
        print(f"   Dias nos metadados: {metadata_days}")
        
        if metadata_days == product.duration_days:
            print("   ✅ CONSISTENTE: Dias batem entre produto e metadados")
        else:
            print("   ❌ INCONSISTENTE: Dias não batem!")
        
    except Exception as e:
        print(f"❌ Erro na simulação: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 VERIFICAÇÃO DOS DIAS DOS PRODUTOS - FOVDARK")
    print("=" * 60)
    print()
    
    # Mostrar produtos atuais
    show_current_products()
    print()
    
    # Testar os dias
    test_products_days()
    
    print()
    print("🔍 SIMULAÇÃO DE COMPRA")
    print("=" * 30)
    
    # Simular compra do primeiro produto ativo
    db = SessionLocal()
    try:
        first_product = db.query(Product).filter(Product.is_active == True).first()
        if first_product:
            print(f"🧪 Testando produto: {first_product.name}")
            simulate_purchase_flow(first_product.id)
        else:
            print("❌ Nenhum produto ativo encontrado para teste")
    finally:
        db.close()
    
    print()
    print("🎯 Verificação concluída!")
