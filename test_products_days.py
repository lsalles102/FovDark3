
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
    print("🎯 Verificação concluída!")
