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

    # Primeiro, tentar obter o domínio customizado
    custom_domain = os.getenv("CUSTOM_DOMAIN")
    if custom_domain:
        # Garantir que tem https://
        if not custom_domain.startswith('http'):
            custom_domain = f"https://{custom_domain}"
        return custom_domain.rstrip('/')

    # Verificar Railway primeiro (tem prioridade)
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    if railway_static_url:
        return railway_static_url.rstrip('/')
    
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_domain:
        return f"https://{railway_public_domain}"
    
    # Verificar variáveis específicas do Railway
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
        # Estamos no Railway mas sem domínio configurado
        print("⚠️ Railway detectado mas sem domínio configurado!")
        return "https://production-railway-app.railway.app"  # placeholder

    # Verificar se estamos no Replit
    replit_slug = os.getenv("REPL_SLUG")
    replit_owner = os.getenv("REPL_OWNER")
    if replit_slug and replit_owner:
        return f"https://{replit_slug}.{replit_owner}.repl.co"

    # Fallback para desenvolvimento local
    return "http://localhost:5000"

def create_payment_preference(plan_id, user_id, user_email, product_id=None):
    """Cria uma preferência de pagamento no Mercado Pago"""
    try:
        print(f"🔍 DEBUG - Iniciando criação de preferência:")
        print(f"  - Plan ID: {plan_id}")
        print(f"  - User ID: {user_id}")
        print(f"  - User Email: {user_email}")
        print(f"  - Product ID: {product_id}")

        if not mp:
            print("❌ MercadoPago SDK não inicializado")
            print(f"❌ Token configurado: {bool(MERCADOPAGO_ACCESS_TOKEN)}")
            return {
                "error": "Integração do Mercado Pago não configurada. Configure o MERCADOPAGO_ACCESS_TOKEN nas variáveis de ambiente."
            }

        # Validações básicas
        if not user_email or "@" not in user_email:
            print(f"❌ Email inválido: {user_email}")
            return {"error": "Email do usuário inválido"}

        if not user_id or user_id <= 0:
            print(f"❌ User ID inválido: {user_id}")
            return {"error": "ID do usuário inválido"}

        # Se product_id for fornecido, buscar produto do banco
        if product_id:
            from models import Product
            db = next(get_db())
            produto_db = db.query(Product).filter(Product.id == product_id).first()
            db.close()

            if not produto_db:
                print(f"❌ Produto ID {product_id} não encontrado no banco")
                return {"error": "Produto não encontrado"}

            print(f"✅ Produto encontrado no banco:")
            print(f"   - Nome: {produto_db.name}")
            print(f"   - Dias configurados: {produto_db.duration_days}")
            print(f"   - Preço: R$ {produto_db.price}")
            print(f"   - ID: {produto_db.id}")

            product_info = {
                'name': produto_db.name,
                'description': produto_db.description or f"Acesso por {produto_db.duration_days} dias",
                'price': float(produto_db.price),
                'days': produto_db.duration_days,
                'currency': 'BRL'
            }

            print(f"🔍 Product info criado com {product_info['days']} dias")
        else:
            # Usar produtos legados
            if plan_id not in PRODUCTS:
                return {"error": f"Plano {plan_id} não encontrado"}
            product_info = PRODUCTS[plan_id]

        # Validações de preço e produto
        price = float(product_info['price'])
        if price < 0.50:
            print(f"❌ Preço muito baixo: R$ {price:.2f}")
            return {"error": f"Valor mínimo é R$ 0,50. Valor informado: R$ {price:.2f}"}

        if price > 50000:
            print(f"❌ Preço muito alto: R$ {price:.2f}")
            return {"error": f"Valor muito alto. Máximo permitido: R$ 50.000,00"}

        if product_info['days'] <= 0:
            print(f"❌ Duração inválida: {product_info['days']} dias")
            return {"error": "Duração do produto deve ser maior que zero"}

        domain_url = get_domain()
        print(f"🌐 Domínio configurado: {domain_url}")

        # Sanitizar dados da preferência
        item_title = str(product_info['name'])[:256]  # Limitar título
        item_description = str(product_info['description'])[:600]  # Limitar descrição

        preference_data = {
            "items": [
                {
                    "title": item_title,
                    "description": item_description,
                    "quantity": 1,
                    "currency_id": "BRL",  # Fixar moeda
                    "unit_price": round(float(product_info['price']), 2)  # Arredondar preço
                }
            ],
            "payer": {
                "email": user_email.lower().strip(),
                "name": user_email.split("@")[0][:64],  # Limitar nome
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
        print(f"📋 Metadados que serão enviados:")
        print(f"  - Plan ID: {plan_id}")
        print(f"  - Product ID: {product_id}")
        print(f"  - Days: {product_info['days']} (valor obtido do produto)")
        print(f"  - User ID: {user_id}")
        print(f"  - User Email: {user_email}")
        print(f"  - Environment: {'production' if 'TEST' not in MERCADOPAGO_ACCESS_TOKEN else 'test'}")

        print(f"🔍 Dados completos da preferência:")
        print(f"  - Item: {product_info['name']} - R$ {product_info['price']}")
        print(f"  - Descrição: {product_info['description']}")
        print(f"  - Duração configurada: {product_info['days']} dias")

        print(f"📋 Dados da preferência que será enviada:")
        print(f"  - Título: {item_title}")
        print(f"  - Preço: R$ {product_info['price']:.2f}")
        print(f"  - Email: {user_email}")
        print(f"  - Domínio: {domain_url}")

        try:
            preference_response = mp.preference().create(preference_data)
            print(f"📊 Status da resposta: {preference_response.get('status')}")

            if preference_response.get("status") not in [200, 201]:
                print(f"❌ Resposta de erro da API: {preference_response}")
                error_message = "Erro desconhecido"

                if "response" in preference_response:
                    response_data = preference_response["response"]
                    if "message" in response_data:
                        error_message = response_data["message"]
                    elif "cause" in response_data:
                        error_message = str(response_data["cause"])

                return {"error": f"Erro do MercadoPago: {error_message}"}

        except Exception as api_error:
            print(f"❌ Exceção na API do MercadoPago: {api_error}")
            print(f"❌ Tipo do erro: {type(api_error)}")
            return {"error": f"Erro de comunicação com MercadoPago: {str(api_error)}"}

        if preference_response["status"] == 201:
            print("✅ Preferência criada com sucesso no Mercado Pago")
            response_data = preference_response["response"]
            print(f"🔗 URLs de checkout retornadas:")
            print(f"  - Init Point: {response_data.get('init_point')}")
            print(f"  - Sandbox Init Point: {response_data.get('sandbox_init_point')}")
            return response_data
        else:
            print(f"❌ Status inesperado: {preference_response}")
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
                plan_name = metadata.get("plan_id", "Plano Padrão")
                product_id = metadata.get("product_id")
                if product_id and product_id.isdigit():
                    product_id = int(product_id)
                else:
                    product_id = None

        print(f"🔍 Debug - Preference ID: {preference_id}")
        print(f"🔍 Debug - Product ID obtido dos metadados: {product_id}")
        print(f"🔍 Debug - Plan Name: {plan_name}")

        # SEMPRE buscar os dias do produto no banco de dados primeiro
        if product_id:
            try:
                from models import Product
                produto_db = db.query(Product).filter(Product.id == product_id).first()
                if produto_db:
                    days_to_add = produto_db.duration_days
                    plan_name = produto_db.name
                    print(f"✅ Dias obtidos do produto no banco (ID {product_id}): {days_to_add}")
                else:
                    print(f"❌ Produto ID {product_id} não encontrado no banco")
            except Exception as e:
                print(f"⚠️ Erro ao buscar produto do banco: {e}")

        # Fallback para planos legados APENAS se não conseguiu obter do banco
        if days_to_add == 1 and plan_name in PRODUCTS:
            days_to_add = PRODUCTS[plan_name]["days"]
            print(f"🔄 Fallback - Dias obtidos dos produtos legados: {days_to_add}")

        # Se ainda não conseguiu obter dias válidos, usar o valor dos metadados como último recurso
        if days_to_add == 1 and preference_id:
            try:
                metadata_days = int(metadata.get("days", 1))
                if metadata_days > 1:
                    days_to_add = metadata_days
                    print(f"🔄 Usando dias dos metadados: {days_to_add}")
            except:
                pass

        print(f"📅 RESULTADO FINAL: Adicionando {days_to_add} dias ao usuário")
        print(f"🏷️ Nome do plano: {plan_name}")

        # Validação final para garantir que não adicionamos apenas 1 dia por erro
        if days_to_add <= 1:
            print(f"⚠️ AVISO: Apenas {days_to_add} dia(s) sendo adicionado(s). Isso pode ser um erro!")
            print(f"🔍 Verificando se é o produto de teste...")

        # Log final de debug
        print(f"🔍 Debug final:")
        print(f"  - Product ID final: {product_id}")
        print(f"  - Dias finais: {days_to_add}")
        print(f"  - Nome do plano final: {plan_name}")
        print(f"  - Metadados: {metadata if 'metadata' in locals() else 'Nenhum'}")

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