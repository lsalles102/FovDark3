
#!/usr/bin/env python3

import os
import mercadopago
from datetime import datetime

# Configurar SDK do MercadoPago
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

if not MERCADOPAGO_ACCESS_TOKEN:
    print("❌ MERCADOPAGO_ACCESS_TOKEN não configurado")
    exit(1)

mp = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

def create_test_users():
    """Criar usuários de teste para o Mercado Pago"""
    try:
        print("🔄 Criando usuários de teste...")
        
        # Dados para criar usuários de teste (vendedor e comprador)
        users_data = [
            {"site_id": "MLB"},  # Comprador
            {"site_id": "MLB"}   # Vendedor
        ]
        
        created_users = []
        
        for i, user_data in enumerate(users_data):
            try:
                # Usar a API correta para criar usuários de teste
                response = mp.test_user().create(user_data)
                
                if response["status"] == 201:
                    user = response["response"]
                    user_type = "Comprador" if i == 0 else "Vendedor"
                    print(f"\n✅ {user_type} de teste criado com sucesso!")
                    print(f"📧 Email: {user['email']}")
                    print(f"🔑 User ID: {user['id']}")
                    print(f"🏦 Access Token: {user['access_token']}")
                    print(f"🏛️ Public Key: {user['public_key']}")
                    
                    created_users.append({
                        "type": user_type,
                        "email": user['email'],
                        "user_id": user['id'],
                        "access_token": user['access_token'],
                        "public_key": user['public_key']
                    })
                else:
                    print(f"❌ Erro ao criar {user_type}: {response}")
                    
            except Exception as e:
                print(f"❌ Erro ao criar usuário {i+1}: {e}")
                continue
        
        return created_users
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return []

def show_test_cards():
    """Mostrar cartões de teste disponíveis"""
    print("\n💳 CARTÕES DE TESTE PARA USAR:")
    
    test_cards = [
        {
            "name": "✅ Visa Aprovado",
            "number": "4235647728025682",
            "security_code": "123",
            "expiration_month": "11",
            "expiration_year": "2025"
        },
        {
            "name": "✅ Mastercard Aprovado", 
            "number": "5031433215406351",
            "security_code": "123",
            "expiration_month": "11",
            "expiration_year": "2025"
        },
        {
            "name": "❌ Visa Rejeitado (para testes)",
            "number": "4000000000000002",
            "security_code": "123", 
            "expiration_month": "11",
            "expiration_year": "2025"
        }
    ]
    
    for card in test_cards:
        print(f"\n🔸 {card['name']}:")
        print(f"   Número: {card['number']}")
        print(f"   CVV: {card['security_code']}")
        print(f"   Validade: {card['expiration_month']}/{card['expiration_year']}")

def show_solution_steps():
    """Mostrar passos para resolver o problema"""
    print("\n" + "="*60)
    print("🔧 COMO RESOLVER O ERRO 'NÃO É POSSÍVEL PAGAR PARA VOCÊ MESMO':")
    print("="*60)
    
    print("\n📋 OPÇÃO 1 - USAR EMAIL DIFERENTE (MAIS SIMPLES):")
    print("1️⃣ Registre uma nova conta no seu site com um email diferente")
    print("2️⃣ Faça login com essa nova conta")
    print("3️⃣ Tente fazer o pagamento novamente")
    print("4️⃣ Use os cartões de teste mostrados acima")
    
    print("\n📋 OPÇÃO 2 - CONFIGURAR USUÁRIOS DE TESTE:")
    print("1️⃣ Execute este script para criar usuários de teste")
    print("2️⃣ Configure as credenciais de teste nos Secrets")
    print("3️⃣ Use o email do usuário comprador para testes")
    
    print("\n⚙️ CREDENCIAIS ATUAIS:")
    print(f"🔑 Access Token: {'***CONFIGURADO***' if MERCADOPAGO_ACCESS_TOKEN else '❌ NÃO CONFIGURADO'}")
    print(f"🏛️ Ambiente: {'🧪 TESTE' if 'TEST' in MERCADOPAGO_ACCESS_TOKEN else '🏭 PRODUÇÃO'}")

def main():
    print("🚀 SOLUCIONADOR DE PROBLEMAS - MERCADO PAGO")
    print("=" * 60)
    
    # Verificar ambiente
    if "TEST" in MERCADOPAGO_ACCESS_TOKEN:
        print("✅ Detectado modo TESTE - OK para desenvolvimento")
    else:
        print("⚠️  Detectado modo PRODUÇÃO - Cuidado com testes!")
    
    # Mostrar solução
    show_solution_steps()
    
    # Mostrar cartões de teste
    show_test_cards()
    
    # Tentar criar usuários de teste (pode falhar com credenciais de produção)
    print("\n🔄 Tentando criar usuários de teste...")
    users = create_test_users()
    
    if users:
        print(f"\n✅ {len(users)} usuários de teste criados!")
        for user in users:
            print(f"\n👤 {user['type']}:")
            print(f"   📧 Email: {user['email']}")
            print(f"   🔑 Access Token: {user['access_token'][:20]}...")
    else:
        print("\n❌ Não foi possível criar usuários de teste")
        print("💡 Use a OPÇÃO 1 (email diferente) que é mais simples!")
    
    print("\n" + "="*60)
    print("✅ RESUMO DA SOLUÇÃO:")
    print("📧 Use um EMAIL DIFERENTE para fazer o teste de pagamento")
    print("💳 Use os cartões de teste mostrados acima")
    print("🔒 Certifique-se de estar em modo TESTE se possível")
    print("="*60)

if __name__ == "__main__":
    main()
