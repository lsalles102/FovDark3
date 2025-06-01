
#!/usr/bin/env python3

import os
import requests
from mercadopago_integration import get_domain, MERCADOPAGO_ACCESS_TOKEN, mp

def check_railway_configuration():
    """Verificar e corrigir configuração do Railway"""
    print("🔍 Verificando configuração do Railway...")
    
    # 1. Verificar se estamos no Railway
    is_railway = bool(
        os.getenv("RAILWAY_STATIC_URL") or 
        os.getenv("RAILWAY_PUBLIC_DOMAIN") or
        os.getenv("RAILWAY_ENVIRONMENT") or
        os.getenv("RAILWAY_PROJECT_ID")
    )
    
    print(f"🏗️ Ambiente Railway detectado: {'SIM' if is_railway else 'NÃO'}")
    
    if not is_railway:
        print("❌ Este script deve ser executado no Railway")
        return False
    
    # 2. Verificar domínio
    domain = get_domain()
    print(f"🌐 Domínio detectado: {domain}")
    
    # 3. Verificar variáveis de ambiente importantes
    env_vars = {
        "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL"),
        "RAILWAY_PUBLIC_DOMAIN": os.getenv("RAILWAY_PUBLIC_DOMAIN"),
        "CUSTOM_DOMAIN": os.getenv("CUSTOM_DOMAIN"),
        "MERCADOPAGO_ACCESS_TOKEN": "CONFIGURADO" if MERCADOPAGO_ACCESS_TOKEN else "NÃO CONFIGURADO",
        "DATABASE_URL": "CONFIGURADO" if os.getenv("DATABASE_URL") else "NÃO CONFIGURADO",
        "PORT": os.getenv("PORT", "5000")
    }
    
    print("\n📋 Variáveis de ambiente:")
    for key, value in env_vars.items():
        status = "✅" if value and value != "NÃO CONFIGURADO" else "❌"
        print(f"  {status} {key}: {value}")
    
    # 4. Testar MercadoPago
    if MERCADOPAGO_ACCESS_TOKEN and mp:
        print(f"\n💳 Testando MercadoPago...")
        
        # Testar criação de preferência
        test_preference = {
            "items": [{
                "title": "Teste Railway",
                "quantity": 1,
                "unit_price": 1.00,
                "currency_id": "BRL"
            }],
            "back_urls": {
                "success": f"{domain}/success",
                "failure": f"{domain}/cancelled",
                "pending": f"{domain}/pending"
            },
            "notification_url": f"{domain}/api/webhook/mercadopago"
        }
        
        try:
            response = mp.preference().create(test_preference)
            if response["status"] == 201:
                print("✅ MercadoPago funcionando corretamente")
                print(f"🔗 Webhook URL: {domain}/api/webhook/mercadopago")
                return True
            else:
                print(f"❌ Erro no MercadoPago: {response}")
                return False
        except Exception as e:
            print(f"❌ Exceção no MercadoPago: {e}")
            return False
    else:
        print("❌ MercadoPago não configurado")
        return False

def suggest_fixes():
    """Sugerir correções"""
    print("\n🔧 SOLUÇÕES RECOMENDADAS:")
    
    domain = get_domain()
    
    print("1. Configurar variáveis no Railway:")
    print(f"   CUSTOM_DOMAIN=https://seu-dominio.com")
    print(f"   MERCADOPAGO_ACCESS_TOKEN=seu_token_aqui")
    
    print("\n2. Configurar webhook no MercadoPago:")
    print(f"   URL: {domain}/api/webhook/mercadopago")
    print(f"   Eventos: payment")
    
    print("\n3. Verificar se o domínio está acessível:")
    print(f"   Teste: {domain}/api/mercadopago/status")

if __name__ == "__main__":
    success = check_railway_configuration()
    if not success:
        suggest_fixes()
    
    print(f"\n{'🎉 CONFIGURAÇÃO OK!' if success else '⚠️ CORREÇÕES NECESSÁRIAS'}")
