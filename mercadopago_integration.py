import os
print(f"🚀 DEBUG ENV VAR: MERCADOPAGO_ACCESS_TOKEN = {os.getenv('MERCADOPAGO_ACCESS_TOKEN')}")
print(f"🔍 TODAS AS VARIÁVEIS: {dict(os.environ)}")
import mercadopago
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models import User, Payment

# Configuração do MercadoPago
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

# Verificar se o token existe
if not MERCADOPAGO_ACCESS_TOKEN:
    print("⚠️ AVISO: MERCADOPAGO_ACCESS_TOKEN não encontrado!")
    print("⚠️ Configure a variável de ambiente para processar pagamentos")
    mp = None
else:
    try:
        mp = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
        token_type = "TESTE" if "TEST" in MERCADOPAGO_ACCESS_TOKEN else "PRODUÇÃO"
        print(f"✅ MercadoPago inicializado em modo {token_type}")
    except Exception as e:
        print(f"❌ Erro ao inicializar MercadoPago: {e}")
        mp = None

# Definição dos produtos
PRODUCTS = {
    'mensal': {
        'name': 'Plano Mensal - FovDark',
        'description': 'Acesso completo por 1 mês ao melhor aimbot',
        'price': 79.90,
        'days': 30,
        'currency': 'BRL'
    },
    'trimestral': {
        'name': 'Plano Trimestral - FovDark',
        'description': 'Acesso completo por 3 meses com desconto',
        'price': 199.90,
        'days': 90,
        'currency': 'BRL'
    },
    'anual': {
        'name': 'Plano Anual - FovDark',
        'description': 'Acesso completo por 1 ano com maior desconto',
        'price': 299.90,
        'days': 365,
        'currency': 'BRL'
    }
}

def get_domain():
    """Retorna o domínio base da aplicação"""
    import os
    
    # Primeiro, tentar obter o domínio do Replit
    replit_domains = os.getenv("REPLIT_DOMAINS")
    if replit_domains:
        # REPLIT_DOMAINS contém o domínio principal
        return f"https://{replit_domains}"
    
    # Tentar Railway
    try:
        from railway_config import get_railway_domain, is_railway_environment
        if is_railway_environment():
            return get_railway_domain()
    except ImportError:
        pass

    # Fallback para desenvolvimento local
    return "http://localhost:5000"

def create_payment_preference(plan_id, user_id, user_email, product_id=None):
    """Cria uma preferência de pagamento no Mercado Pago"""
    try:
        if not mp:
            print("❌ MercadoPago SDK não inicializado")
            print(f"❌ Token configurado: {bool(MERCADOPAGO_ACCESS_TOKEN)}")
            return {
                "error": "Integração do Mercado Pago não configurada. Configure o MERCADOPAGO_ACCESS_TOKEN nas variáveis de ambiente."
            }

        # Se product_id for fornecido, buscar produto do banco
        if product_id:
            from models import Product
            db = next(get_db())
            produto_db = db.query(Product).filter(Product.id == product_id).first()
            db.close()

            if not produto_db:
                return {"error": "Produto não encontrado"}

            product_info = {
                'name': produto_db.name,
                'description': produto_db.description or f"Acesso por {produto_db.duration_days} dias",
                'price': float(produto_db.price),
                'days': produto_db.duration_days,
                'currency': 'BRL'
            }
        else:
            # Usar produtos legados
            if plan_id not in PRODUCTS:
                return {"error": f"Plano {plan_id} não encontrado"}
            product_info = PRODUCTS[plan_id]

        # Validar preço mínimo (MercadoPago tem valor mínimo de R$ 0.50)
        if product_info['price'] < 0.50:
            return {"error": f"Valor mínimo é R$ 0,50. Valor informado: R$ {product_info['price']:.2f}"}

        domain_url = get_domain()

        preference_data = {
            "items": [
                {
                    "title": product_info['name'],
                    "description": product_info['description'],
                    "quantity": 1,
                    "currency_id": product_info['currency'],
                    "unit_price": product_info['price']
                }
            ],
            "payer": {
                "email": user_email,
                "name": user_email.split("@")[0],
                "surname": "Cliente"
            },
            "back_urls": {
                "success": f"{domain_url}/success",
                "failure": f"{domain_url}/cancelled", 
                "pending": f"{domain_url}/pending"
            },
            "auto_return": "approved",
            "external_reference": f"user_{user_id}_product_{product_id or plan_id}",
            "metadata": {
                "plan_id": plan_id,
                "product_id": str(product_id) if product_id else "",
                "days": str(product_info['days']),
                "user_id": str(user_id),
                "user_email": user_email,
                "environment": "production" if "TEST" not in MERCADOPAGO_ACCESS_TOKEN else "test"
            },
            "notification_url": f"{domain_url}/api/webhook/mercadopago",
            "statement_descriptor": "FOVDARK",
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 12
            },
            "expires": True,
            "expiration_date_from": datetime.utcnow().isoformat(),
            "expiration_date_to": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

        print(f"🔄 Criando preferência no Mercado Pago para usuário {user_id}")
        print(f"💰 Produto: {product_info['name']} - R$ {product_info['price']}")
        print(f"🌐 Domínio configurado: {domain_url}")
        print(f"🔑 Token tipo: {'TESTE' if 'TEST' in MERCADOPAGO_ACCESS_TOKEN else 'PRODUÇÃO'}")
        print(f"📋 URLs de retorno:")
        print(f"  - Success: {domain_url}/success")
        print(f"  - Failure: {domain_url}/cancelled")
        print(f"  - Pending: {domain_url}/pending")
        print(f"📧 Webhook URL: {domain_url}/api/webhook/mercadopago")
        print(f"📋 Metadados enviados:")
        print(f"  - Plan ID: {plan_id}")
        print(f"  - Product ID: {product_id}")
        print(f"  - Days: {product_info['days']}")
        print(f"  - User ID: {user_id}")
        print(f"  - User Email: {user_email}")

        try:
            preference_response = mp.preference().create(preference_data)
            print(f"📊 Status da resposta: {preference_response.get('status')}")
            print(f"📊 Resposta: {preference_response}")
        except Exception as api_error:
            print(f"❌ Erro na API do MercadoPago: {api_error}")
            return {"error": f"Erro na API do MercadoPago: {str(api_error)}"}

        if preference_response["status"] == 201:
            print("✅ Preferência criada com sucesso no Mercado Pago")
            response_data = preference_response["response"]
            print(f"🔗 URLs de checkout retornadas:")
            print(f"  - Init Point: {response_data.get('init_point')}")
            print(f"  - Sandbox Init Point: {response_data.get('sandbox_init_point')}")
            return response_data
        else:
            print(f"❌ Erro ao criar preferência: {preference_response}")
            return {'error': 'Erro ao criar preferência de pagamento'}

    except Exception as e:
        print(f"❌ Erro na integração do Mercado Pago: {str(e)}")
        return {'error': f'Erro interno: {str(e)}'}

def handle_payment_notification(payment_data):
    """Processa notificação de pagamento do Mercado Pago"""
    try:
        if not mp:
            return False, "MercadoPago não configurado"

        print(f"🔔 Recebendo notificação do Mercado Pago: {payment_data}")

        # Obter dados do pagamento
        payment_id = payment_data.get("data", {}).get("id")
        if not payment_id:
            return False, "ID do pagamento não encontrado"

        print(f"💳 Processando pagamento ID: {payment_id}")

        # Buscar informações do pagamento no Mercado Pago
        payment_info = mp.payment().get(payment_id)

        if payment_info["status"] != 200:
            print(f"❌ Erro ao buscar pagamento: {payment_info}")
            return False, "Erro ao buscar informações do pagamento"

        payment_details = payment_info["response"]
        print(f"📊 Status do pagamento: {payment_details['status']}")

        # Verificar se o pagamento foi aprovado
        if payment_details["status"] != "approved":
            print(f"⏳ Pagamento ainda não aprovado: {payment_details['status']}")
            return True, f"Pagamento com status: {payment_details['status']}"

        # Obter dados do usuário da referência externa
        external_reference = payment_details.get("external_reference", "")
        if not external_reference:
            return False, "Referência externa não encontrada"

        # Extrair user_id da referência
        try:
            user_id = int(external_reference.split("_")[1])
        except (IndexError, ValueError):
            return False, "Formato de referência externa inválido"

        print(f"👤 Processando para usuário ID: {user_id}")

        # Conectar ao banco
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.close()
            return False, "Usuário não encontrado"

        # Verificar se o pagamento já foi processado
        existing_payment = db.query(Payment).filter(
            Payment.gateway_id == str(payment_id)
        ).first()

        if existing_payment:
            db.close()
            return True, "Pagamento já processado"

        # Obter metadados da preferência
        preference_id = payment_details.get("preference_id")
        days_to_add = 1  # Padrão mínimo
        plan_name = "Plano Padrão"
        product_id = None

        if preference_id:
            preference_info = mp.preference().get(preference_id)
            if preference_info["status"] == 200:
                metadata = preference_info["response"].get("metadata", {})
                days_to_add = int(metadata.get("days", 1))
                plan_name = metadata.get("plan_id", "Plano Padrão")
                product_id = metadata.get("product_id")
                if product_id and product_id.isdigit():
                    product_id = int(product_id)
                else:
                    product_id = None
        
        # Se não conseguir obter dos metadados, tentar buscar diretamente do produto
        if product_id and days_to_add == 1:
            try:
                from models import Product
                produto_db = db.query(Product).filter(Product.id == product_id).first()
                if produto_db:
                    days_to_add = produto_db.duration_days
                    plan_name = produto_db.name
                    print(f"🔍 Dias obtidos do produto no banco: {days_to_add}")
            except Exception as e:
                print(f"⚠️ Erro ao buscar produto do banco: {e}")
        
        # Fallback para planos legados
        if days_to_add == 1 and plan_name in PRODUCTS:
            days_to_add = PRODUCTS[plan_name]["days"]
            print(f"🔍 Dias obtidos dos produtos legados: {days_to_add}")

        print(f"📅 Adicionando {days_to_add} dias ao usuário")
        print(f"🔍 Debug - Preference ID: {preference_id}")
        print(f"🔍 Debug - Product ID: {product_id}")
        print(f"🔍 Debug - Plan Name: {plan_name}")
        print(f"🔍 Debug - Metadados obtidos: {metadata if 'metadata' in locals() else 'Nenhum'}")

        # Criar registro de pagamento
        payment = Payment(
            user_id=user_id,
            product_id=product_id,
            valor=payment_details["transaction_amount"],
            status='completed',
            plano=plan_name,
            gateway_id=str(payment_id),
            data_pagamento=datetime.utcnow()
        )
        db.add(payment)

        # Atualizar licença do usuário
        if user.data_expiracao and user.data_expiracao > datetime.utcnow():
            # Estender licença existente
            user.data_expiracao = user.data_expiracao + timedelta(days=days_to_add)
            print(f"⏰ Licença estendida até: {user.data_expiracao}")
        else:
            # Nova licença
            user.data_expiracao = datetime.utcnow() + timedelta(days=days_to_add)
            print(f"🆕 Nova licença criada até: {user.data_expiracao}")

        user.status_licenca = "ativa"

        db.commit()
        db.close()

        print(f"✅ Pagamento processado com sucesso para {user.email}")
        return True, "Pagamento processado com sucesso"

    except Exception as e:
        print(f"❌ Erro ao processar notificação: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False, str(e)

def get_plan_details(plan_id):
    """Retorna os detalhes de um plano"""
    if plan_id in PRODUCTS:
        return PRODUCTS[plan_id]
    return None

def activate_user_license(user_id, plan_id):
    """Ativar licença do usuário após pagamento aprovado - para testes"""
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            db.close()
            return False, "Usuário não encontrado"

        plan = PRODUCTS.get(plan_id)
        if not plan:
            db.close()
            return False, "Plano inválido"

        # Calcular nova data de expiração
        if user.data_expiracao and user.data_expiracao > datetime.utcnow():
            # Estender licença existente
            new_expiration = user.data_expiracao + timedelta(days=plan["days"])
        else:
            # Nova licença
            new_expiration = datetime.utcnow() + timedelta(days=plan["days"])

        user.data_expiracao = new_expiration
        user.status_licenca = "ativa"

        # Criar registro de pagamento
        payment = Payment(
            user_id=user_id,
            valor=plan["price"],
            plano=plan_id,
            status="completed",
            gateway_id=f"test_payment_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            data_pagamento=datetime.utcnow()
        )

        db.add(payment)
        db.commit()
        db.close()

        return True, f"Licença ativada até {new_expiration.strftime('%d/%m/%Y')}"

    except Exception as e:
        if 'db' in locals():
            db.rollback()
            db.close()
        return False, f"Erro ao ativar licença: {str(e)}"