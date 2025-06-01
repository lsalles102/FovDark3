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

        # Criar referência externa mais robusta
        external_ref = f"user_{user_id}_product_{product_id or plan_id}"
        
        # Criar metadados completos
        metadata = {
            "plan_id": str(plan_id),
            "product_id": str(product_id) if product_id else "",
            "days": str(product_info['days']),
            "user_id": str(user_id),
            "user_email": user_email,
            "environment": "production" if "TEST" not in MERCADOPAGO_ACCESS_TOKEN else "test",
            "created_at": datetime.utcnow().isoformat(),
            "domain": domain_url
        }
        
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
            "external_reference": external_ref,
            "metadata": metadata,
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
        
        print(f"📋 DADOS DA PREFERÊNCIA CRIADA:")
        print(f"   - External Reference: {external_ref}")
        print(f"   - Metadados: {metadata}")
        print(f"   - Webhook URL: {domain_url}/api/webhook/mercadopago")
        print(f"   - Item: {item_title} - R$ {product_info['price']}")
        print(f"   - Dias configurados: {product_info['days']}")
        print(f"   - Product ID: {product_id}")
        print(f"   - Plan ID: {plan_id}")

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
            print("❌ ID do pagamento não encontrado na notificação")
            return False, "ID do pagamento não encontrado"

        print(f"💳 Processando pagamento ID: {payment_id}")

        # Buscar informações do pagamento no Mercado Pago
        try:
            payment_info = mp.payment().get(payment_id)
        except Exception as api_error:
            print(f"❌ Erro na API do MercadoPago: {api_error}")
            return False, f"Erro na API: {str(api_error)}"

        if payment_info["status"] != 200:
            print(f"❌ Erro ao buscar pagamento: {payment_info}")
            return False, "Erro ao buscar informações do pagamento"

        payment_details = payment_info["response"]
        print(f"📊 Status do pagamento recebido: {payment_details['status']}")
        print(f"💰 Valor do pagamento: R$ {payment_details.get('transaction_amount', 0)}")

        # Verificar se o pagamento foi aprovado
        if payment_details["status"] != "approved":
            print(f"⏳ Pagamento ainda não aprovado: {payment_details['status']}")
            # Atualizar status se existe pagamento pendente
            db = next(get_db())
            try:
                pending_payment = db.query(Payment).filter(
                    Payment.gateway_id == str(payment_id)
                ).first()
                if pending_payment:
                    pending_payment.status = payment_details["status"]
                    db.commit()
                    print(f"🔄 Status do pagamento atualizado para: {payment_details['status']}")
            except Exception as e:
                print(f"⚠️ Erro ao atualizar status pendente: {e}")
            finally:
                db.close()
            
            return True, f"Pagamento com status: {payment_details['status']}"

        # Obter dados do usuário da referência externa
        external_reference = payment_details.get("external_reference", "")
        print(f"🔍 Referência externa: {external_reference}")
        
        if not external_reference:
            print("❌ Referência externa não encontrada")
            return False, "Referência externa não encontrada"

        # Extrair user_id e product_id da referência
        try:
            # Formato: user_{user_id}_product_{product_id} ou user_{user_id}_product_{plan_id}
            parts = external_reference.split("_")
            user_id = int(parts[1])
            
            # Tentar obter product_id se presente
            product_id = None
            if len(parts) >= 4 and parts[3].isdigit():
                product_id = int(parts[3])
            
            print(f"👤 User ID extraído: {user_id}")
            print(f"📦 Product ID extraído: {product_id}")
            
        except (IndexError, ValueError) as e:
            print(f"❌ Erro ao extrair dados da referência: {e}")
            return False, "Formato de referência externa inválido"

        # Conectar ao banco
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"❌ Usuário ID {user_id} não encontrado no banco")
                return False, "Usuário não encontrado"

            print(f"👤 Usuário encontrado: {user.email}")

            # Verificar se o pagamento já foi processado
            existing_payment = db.query(Payment).filter(
                Payment.gateway_id == str(payment_id)
            ).first()

            if existing_payment and existing_payment.status == "completed":
                print(f"✅ Pagamento já processado anteriormente")
                return True, "Pagamento já processado"

            # Obter informações do produto e plano
            days_to_add = 30  # Padrão
            plan_name = "Plano Padrão"
            actual_product_id = product_id

            # PRIORIDADE 1: Buscar produto no banco de dados
            if product_id:
                try:
                    from models import Product
                    produto_db = db.query(Product).filter(Product.id == product_id).first()
                    if produto_db:
                        days_to_add = produto_db.duration_days
                        plan_name = produto_db.name
                        print(f"✅ Produto encontrado no banco:")
                        print(f"   - ID: {produto_db.id}")
                        print(f"   - Nome: {produto_db.name}")
                        print(f"   - Dias: {produto_db.duration_days}")
                        print(f"   - Preço: R$ {produto_db.price}")
                    else:
                        print(f"❌ Produto ID {product_id} não encontrado no banco")
                        actual_product_id = None
                except Exception as e:
                    print(f"⚠️ Erro ao buscar produto do banco: {e}")
                    actual_product_id = None

            # PRIORIDADE 2: Buscar nos metadados da preferência
            preference_id = payment_details.get("preference_id")
            if preference_id:
                try:
                    preference_info = mp.preference().get(preference_id)
                    if preference_info["status"] == 200:
                        metadata = preference_info["response"].get("metadata", {})
                        print(f"📋 Metadados da preferência: {metadata}")
                        
                        # Se não conseguiu do banco, tentar dos metadados
                        if days_to_add == 30:  # Ainda é o padrão
                            metadata_days = metadata.get("days")
                            if metadata_days and str(metadata_days).isdigit():
                                days_to_add = int(metadata_days)
                                print(f"📅 Dias obtidos dos metadados: {days_to_add}")
                        
                        # Atualizar plan_name se disponível
                        metadata_plan = metadata.get("plan_id")
                        if metadata_plan:
                            plan_name = metadata_plan
                            print(f"🏷️ Nome do plano dos metadados: {plan_name}")
                        
                        # Verificar product_id nos metadados se não temos
                        if not actual_product_id:
                            metadata_product_id = metadata.get("product_id")
                            if metadata_product_id and str(metadata_product_id).isdigit():
                                actual_product_id = int(metadata_product_id)
                                print(f"📦 Product ID dos metadados: {actual_product_id}")
                                
                                # Tentar buscar produto novamente
                                try:
                                    produto_db = db.query(Product).filter(Product.id == actual_product_id).first()
                                    if produto_db:
                                        days_to_add = produto_db.duration_days
                                        plan_name = produto_db.name
                                        print(f"✅ Produto encontrado via metadados: {produto_db.name} - {days_to_add} dias")
                                except Exception as e:
                                    print(f"⚠️ Erro ao buscar produto via metadados: {e}")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao buscar metadados da preferência: {e}")

            # PRIORIDADE 3: Fallback para planos legados
            if days_to_add == 30 and plan_name in PRODUCTS:
                days_to_add = PRODUCTS[plan_name]["days"]
                print(f"🔄 Fallback para plano legado: {plan_name} - {days_to_add} dias")

            # Validação final
            if days_to_add <= 0:
                days_to_add = 30
                print(f"⚠️ Dias inválidos, usando padrão: {days_to_add} dias")

            print(f"📅 RESULTADO FINAL:")
            print(f"   - Usuário: {user.email}")
            print(f"   - Produto ID: {actual_product_id}")
            print(f"   - Plano: {plan_name}")
            print(f"   - Dias a adicionar: {days_to_add}")
            print(f"   - Valor: R$ {payment_details['transaction_amount']}")

            # Atualizar ou criar registro de pagamento
            if existing_payment:
                existing_payment.status = 'completed'
                existing_payment.product_id = actual_product_id
                existing_payment.plano = plan_name
                existing_payment.data_pagamento = datetime.utcnow()
                print(f"🔄 Pagamento existente atualizado")
            else:
                payment = Payment(
                    user_id=user_id,
                    product_id=actual_product_id,
                    valor=payment_details["transaction_amount"],
                    status='completed',
                    plano=plan_name,
                    gateway_id=str(payment_id),
                    data_pagamento=datetime.utcnow()
                )
                db.add(payment)
                print(f"🆕 Novo registro de pagamento criado")

            # Atualizar licença do usuário
            old_expiration = user.data_expiracao
            
            if user.data_expiracao and user.data_expiracao > datetime.utcnow():
                # Estender licença existente
                user.data_expiracao = user.data_expiracao + timedelta(days=days_to_add)
                print(f"⏰ Licença estendida:")
                print(f"   - De: {old_expiration}")
                print(f"   - Para: {user.data_expiracao}")
            else:
                # Nova licença
                user.data_expiracao = datetime.utcnow() + timedelta(days=days_to_add)
                print(f"🆕 Nova licença criada:")
                print(f"   - Válida até: {user.data_expiracao}")

            user.status_licenca = "ativa"
            print(f"✅ Status da licença atualizado para: ativa")

            # Commit das alterações
            db.commit()
            
            print(f"✅ PAGAMENTO PROCESSADO COM SUCESSO!")
            print(f"   - Usuário: {user.email}")
            print(f"   - Valor: R$ {payment_details['transaction_amount']}")
            print(f"   - Produto: {plan_name}")
            print(f"   - Dias adicionados: {days_to_add}")
            print(f"   - Licença válida até: {user.data_expiracao}")
            
            return True, f"Pagamento processado: {plan_name} - {days_to_add} dias adicionados"

        except Exception as e:
            print(f"❌ Erro durante processamento: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False, f"Erro no processamento: {str(e)}"
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Erro crítico ao processar notificação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Erro crítico: {str(e)}"

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