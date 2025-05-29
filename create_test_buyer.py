
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

def create_test_user():
    """Criar usuário de teste para o Mercado Pago"""
    try:
        print("🔄 Criando usuário de teste...")
        
        # Dados para criar usuário de teste
        test_user_data = {
            "json_data": {
                "site_id": "MLB"  # Brasil
            }
        }
        
        # Criar usuário de teste
        response = mp.test_user().create(test_user_data)
        
        if response["status"] == 201:
            user = response["response"]
            print("✅ Usuário de teste criado com sucesso!")
            print(f"📧 Email: {user['email']}")
            print(f"🔑 User ID: {user['id']}")
            print(f"🏦 Access Token: {user['access_token']}")
            print(f"🏛️ Public Key: {user['public_key']}")
            
            # Criar cartões de teste
            create_test_cards(user)
            
            return user
        else:
            print(f"❌ Erro ao criar usuário: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def create_test_cards(user):
    """Criar cartões de teste para o usuário"""
    print("\n💳 Cartões de teste disponíveis:")
    
    test_cards = [
        {
            "name": "Visa Aprovado",
            "number": "4235647728025682",
            "security_code": "123",
            "expiration_month": "11",
            "expiration_year": "2025"
        },
        {
            "name": "Mastercard Aprovado", 
            "number": "5031433215406351",
            "security_code": "123",
            "expiration_month": "11",
            "expiration_year": "2025"
        },
        {
            "name": "Visa Rejeitado",
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

def show_test_credentials():
    """Mostrar credenciais de teste"""
    print("\n🔧 CONFIGURAÇÃO NECESSÁRIA:")
    print("Para testar pagamentos, você precisa:")
    print("1. Usar o email do usuário de teste criado acima")
    print("2. Configurar o Access Token de teste nos Secrets")
    print("3. Usar os cartões de teste para realizar pagamentos")
    
    print("\n⚙️ VARIÁVEIS DE AMBIENTE:")
    print("No painel de Secrets, configure:")
    print("- MERCADOPAGO_ACCESS_TOKEN: (token do usuário vendedor)")
    print("- MERCADOPAGO_PUBLIC_KEY: (chave pública)")

def main():
    print("🚀 Configurando ambiente de teste do Mercado Pago...")
    print("=" * 50)
    
    # Verificar se está em modo sandbox
    if "TEST" in MERCADOPAGO_ACCESS_TOKEN:
        print("✅ Modo sandbox detectado")
    else:
        print("⚠️ Usando credenciais de produção - cuidado!")
    
    # Criar usuário de teste
    test_user = create_test_user()
    
    if test_user:
        show_test_credentials()
        
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Salve as credenciais do usuário de teste")
        print("2. Use um email diferente do vendedor para testar")
        print("3. Use os cartões de teste para pagamentos")
        print("4. Verifique os webhooks no painel do Mercado Pago")
    
    print("\n" + "=" * 50)
    print("✅ Configuração concluída!")

if __name__ == "__main__":
    main()
