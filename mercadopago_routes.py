from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from database import get_db
from models import User, Payment, Product
from auth import get_current_user
from pydantic import BaseModel
from typing import Optional
from mercadopago_integration import (
    create_payment_preference, 
    handle_payment_notification, 
    get_plan_details,
    PRODUCTS
)

router = APIRouter()

class CheckoutRequest(BaseModel):
    plano: str
    product_id: Optional[int] = None

@router.post("/criar-checkout")
async def criar_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar checkout no Mercado Pago"""
    try:
        print(f"🛒 Criando checkout para usuário: {current_user.email}")
        print(f"📦 Dados recebidos: {request}")

        # Buscar produto no banco de dados se product_id fornecido
        if request.product_id:
            produto_db = db.query(Product).filter(
                Product.id == request.product_id,
                Product.is_active == True
            ).first()

            if not produto_db:
                raise HTTPException(status_code=404, detail="Produto não encontrado ou inativo")

            produto_info = {
                "id": produto_db.id,
                "nome": produto_db.name,
                "preco": float(produto_db.price),
                "duracao": produto_db.duration_days
            }
            plan_id = f"product_{produto_db.id}"
        else:
            # Usar produtos legados para compatibilidade
            if request.plano not in PRODUCTS:
                raise HTTPException(status_code=400, detail="Plano não encontrado")

            legacy_plan = PRODUCTS[request.plano]
            produto_info = {
                "id": None,
                "nome": legacy_plan["name"],
                "preco": legacy_plan["price"],
                "duracao": legacy_plan["days"]
            }
            plan_id = request.plano

        # Criar preferência no Mercado Pago
        preference_result = create_payment_preference(
            plan_id=plan_id,
            user_id=current_user.id,
            user_email=current_user.email,
            product_id=request.product_id
        )

        if "error" in preference_result:
            print(f"❌ Erro ao criar preferência: {preference_result['error']}")
            raise HTTPException(status_code=400, detail=preference_result["error"])

        # Registrar pagamento pendente no banco
        pagamento = Payment(
            user_id=current_user.id,
            product_id=request.product_id,
            valor=produto_info["preco"],
            plano=produto_info["nome"],
            gateway_id=preference_result["id"],
            status="pending"
        )

        db.add(pagamento)
        db.commit()
        db.refresh(pagamento)

        print(f"✅ Checkout criado com sucesso - Preference ID: {preference_result['id']}")
        print(f"🔗 Init Point: {preference_result.get('init_point')}")
        print(f"🔗 Sandbox Init Point: {preference_result.get('sandbox_init_point')}")

        # Garantir que temos pelo menos um dos links
        init_point = preference_result.get("init_point")
        sandbox_init_point = preference_result.get("sandbox_init_point")

        # Para ambiente de teste, usar sandbox_init_point, para produção usar init_point
        checkout_url = init_point or sandbox_init_point

        if not checkout_url:
            print("❌ Nenhuma URL de checkout encontrada na resposta do Mercado Pago")
            print(f"❌ Resposta completa: {preference_result}")
            raise HTTPException(status_code=500, detail="Erro: URL de pagamento não gerada pelo Mercado Pago")

        response_data = {
            "success": True,
            "message": "Checkout criado com sucesso",
            "preference_id": preference_result["id"],
            "init_point": init_point,
            "sandbox_init_point": sandbox_init_point
        }

        print(f"📤 Enviando resposta: {response_data}")
        return response_data

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Erro ao criar checkout: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook para receber notificações do Mercado Pago"""
    try:
        print(f"🔔 WEBHOOK MERCADOPAGO RECEBIDO")
        print(f"=" * 50)
        
        # Obter dados do webhook
        body = await request.body()
        print(f"📨 Body recebido: {body}")
        print(f"📋 Headers: {dict(request.headers)}")
        print(f"🌐 URL: {request.url}")
        print(f"🔧 Método: {request.method}")

        # Tentar decodificar como JSON primeiro
        data = {}
        try:
            if body:
                body_str = body.decode('utf-8')
                print(f"📝 Body decodificado: {body_str}")
                data = json.loads(body_str)
                print(f"✅ JSON decodificado com sucesso")
            else:
                print(f"⚠️ Body vazio, tentando form data")
        except json.JSONDecodeError as json_error:
            print(f"❌ Erro ao decodificar JSON: {json_error}")
            # Se não for JSON válido, tentar como form data
            try:
                form_data = await request.form()
                data = dict(form_data)
                print(f"📋 Form data obtido: {data}")
            except Exception as form_error:
                print(f"❌ Erro ao obter form data: {form_error}")
                data = {}

        print(f"📊 Dados finais processados: {data}")
        print(f"🔍 Tipo de notificação: {data.get('type', 'N/A')}")

        # Verificar se é uma notificação de pagamento
        notification_type = data.get("type")
        if notification_type == "payment":
            print(f"💳 Processando notificação de pagamento...")
            
            # Verificar se temos o ID do pagamento
            payment_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) else data.get("id")
            print(f"🆔 Payment ID detectado: {payment_id}")
            
            if not payment_id:
                print(f"❌ Payment ID não encontrado nos dados")
                print(f"🔍 Estrutura dos dados: {data}")
                return {"status": "error", "message": "Payment ID não encontrado"}
            
            try:
                success, message = handle_payment_notification(data)
                
                if success:
                    print(f"✅ WEBHOOK PROCESSADO COM SUCESSO: {message}")
                    return {"status": "ok", "message": message}
                else:
                    print(f"❌ ERRO NO PROCESSAMENTO DO WEBHOOK: {message}")
                    return {"status": "error", "message": message}
                    
            except Exception as process_error:
                print(f"💥 Exceção durante processamento: {process_error}")
                import traceback
                traceback.print_exc()
                return {"status": "error", "message": f"Erro no processamento: {str(process_error)}"}
                
        elif notification_type == "merchant_order":
            print(f"📦 Notificação de merchant_order recebida (ignorando)")
            return {"status": "ok", "message": "Merchant order notification received"}
        elif notification_type == "plan":
            print(f"📋 Notificação de plan recebida (ignorando)")
            return {"status": "ok", "message": "Plan notification received"}
        elif notification_type == "subscription":
            print(f"🔄 Notificação de subscription recebida (ignorando)")
            return {"status": "ok", "message": "Subscription notification received"}
        else:
            print(f"ℹ️ Tipo de notificação desconhecido ou ignorado: {notification_type}")
            print(f"📋 Dados completos: {data}")
            return {"status": "ok", "message": f"Tipo de notificação '{notification_type}' não processado"}

    except Exception as e:
        print(f"💥 ERRO CRÍTICO NO WEBHOOK MERCADOPAGO: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Erro crítico: {str(e)}"}

@router.get("/payment/status/{payment_id}")
async def check_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verificar status de um pagamento específico"""
    try:
        # Buscar pagamento no banco
        payment = db.query(Payment).filter(
            Payment.gateway_id == payment_id,
            Payment.user_id == current_user.id
        ).first()

        if not payment:
            raise HTTPException(status_code=404, detail="Pagamento não encontrado")

        return {
            "payment_id": payment.id,
            "gateway_id": payment.gateway_id,
            "status": payment.status,
            "amount": float(payment.valor),
            "plan": payment.plano,
            "date": payment.data_pagamento.isoformat() if payment.data_pagamento else None,
            "product_id": payment.product_id
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Erro ao verificar status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def get_available_plans():
    """Retorna os planos disponíveis"""
    return PRODUCTS

@router.post("/test-webhook/{payment_id}")
async def test_webhook_processing(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint para testar processamento de webhook com payment_id real"""
    try:
        print(f"🧪 TESTE DE WEBHOOK - Payment ID: {payment_id}")
        
        # Simular dados de webhook do MercadoPago
        test_webhook_data = {
            "type": "payment",
            "data": {
                "id": payment_id
            }
        }
        
        print(f"📊 Dados de teste: {test_webhook_data}")
        
        # Processar usando a função real
        success, message = handle_payment_notification(test_webhook_data)
        
        if success:
            return {
                "success": True,
                "message": f"Teste de webhook bem-sucedido: {message}",
                "payment_id": payment_id
            }
        else:
            return {
                "success": False,
                "message": f"Erro no teste de webhook: {message}",
                "payment_id": payment_id
            }
            
    except Exception as e:
        print(f"❌ Erro no teste de webhook: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no teste: {str(e)}")

@router.get("/debug/payment/{payment_id}")
async def debug_payment_info(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug de informações de pagamento do MercadoPago"""
    try:
        from mercadopago_integration import mp
        
        if not mp:
            raise HTTPException(status_code=500, detail="MercadoPago não configurado")
        
        # Buscar informações do pagamento
        payment_info = mp.payment().get(payment_id)
        
        if payment_info["status"] != 200:
            raise HTTPException(status_code=400, detail=f"Erro ao buscar pagamento: {payment_info}")
        
        payment_details = payment_info["response"]
        
        # Buscar informações da preferência se disponível
        preference_info = None
        preference_id = payment_details.get("preference_id")
        if preference_id:
            pref_response = mp.preference().get(preference_id)
            if pref_response["status"] == 200:
                preference_info = pref_response["response"]
        
        # Buscar pagamento no banco local
        local_payment = db.query(Payment).filter(
            Payment.gateway_id == payment_id
        ).first()
        
        return {
            "payment_details": payment_details,
            "preference_info": preference_info,
            "local_payment": {
                "id": local_payment.id if local_payment else None,
                "user_id": local_payment.user_id if local_payment else None,
                "product_id": local_payment.product_id if local_payment else None,
                "status": local_payment.status if local_payment else None,
                "plano": local_payment.plano if local_payment else None,
                "valor": local_payment.valor if local_payment else None,
            } if local_payment else None
        }
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mercadopago/public-key")
async def get_mercadopago_public_key():
    """Retorna a chave pública do MercadoPago para Secure Fields"""
    try:
        from mercadopago_integration import MERCADOPAGO_ACCESS_TOKEN
        
        if not MERCADOPAGO_ACCESS_TOKEN:
            raise HTTPException(status_code=500, detail="MercadoPago não configurado")
        
        # Determinar chave pública baseada no tipo de token
        if "TEST" in MERCADOPAGO_ACCESS_TOKEN:
            # Ambiente de teste
            public_key = "TEST-c8c68306-c9a2-4ec8-98db-0b00ad3c6dd9"  # Exemplo - substitua pela sua chave de teste
        else:
            # Ambiente de produção
            public_key = "APP_USR-c8c68306-c9a2-4ec8-98db-0b00ad3c6dd9"  # Exemplo - substitua pela sua chave de produção
        
        return {"public_key": public_key}
        
    except Exception as e:
        print(f"❌ Erro ao obter chave pública: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter configuração de pagamento")

class SecurePaymentRequest(BaseModel):
    token: str
    payment_method_id: str
    issuer_id: Optional[int] = None
    installments: int = 1
    product_id: int
    amount: float
    payer: dict

@router.post("/process-secure-payment")
async def process_secure_payment(
    payment_data: SecurePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processar pagamento usando Secure Fields"""
    try:
        from mercadopago_integration import mp, get_domain
        
        if not mp:
            raise HTTPException(status_code=500, detail="MercadoPago não configurado")
        
        # Buscar produto
        product = db.query(Product).filter(
            Product.id == payment_data.product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Validar valor
        if abs(payment_data.amount - float(product.price)) > 0.01:
            raise HTTPException(status_code=400, detail="Valor do pagamento não confere")
        
        # Criar dados do pagamento
        payment_request = {
            "transaction_amount": float(product.price),
            "token": payment_data.token,
            "description": f"{product.name} - {product.duration_days} dias",
            "installments": payment_data.installments,
            "payment_method_id": payment_data.payment_method_id,
            "payer": {
                "email": current_user.email,
                "identification": payment_data.payer["identification"]
            },
            "external_reference": f"user_{current_user.id}_product_{product.id}",
            "metadata": {
                "user_id": str(current_user.id),
                "product_id": str(product.id),
                "days": str(product.duration_days),
                "plan_id": f"product_{product.id}",
                "user_email": current_user.email,
                "created_at": datetime.utcnow().isoformat()
            },
            "notification_url": f"{get_domain()}/api/webhook/mercadopago",
            "statement_descriptor": "FOVDARK"
        }
        
        # Adicionar issuer se fornecido
        if payment_data.issuer_id:
            payment_request["issuer_id"] = payment_data.issuer_id
        
        print(f"💳 Processando pagamento seguro:")
        print(f"  - Usuário: {current_user.email}")
        print(f"  - Produto: {product.name}")
        print(f"  - Valor: R$ {product.price}")
        print(f"  - Token: {payment_data.token[:20]}...")
        
        # Enviar para MercadoPago
        payment_response = mp.payment().create(payment_request)
        
        if payment_response["status"] not in [200, 201]:
            print(f"❌ Erro na resposta do MercadoPago: {payment_response}")
            raise HTTPException(status_code=400, detail="Erro no processamento do pagamento")
        
        payment_result = payment_response["response"]
        
        # Registrar pagamento no banco
        payment_record = Payment(
            user_id=current_user.id,
            product_id=product.id,
            valor=float(product.price),
            plano=product.name,
            gateway_id=str(payment_result["id"]),
            status=payment_result["status"],
            data_pagamento=datetime.utcnow()
        )
        
        db.add(payment_record)
        db.commit()
        
        print(f"✅ Pagamento registrado:")
        print(f"  - ID MercadoPago: {payment_result['id']}")
        print(f"  - Status: {payment_result['status']}")
        print(f"  - Método: {payment_result.get('payment_method_id')}")
        
        # Se aprovado, ativar licença imediatamente
        if payment_result["status"] == "approved":
            if current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow():
                current_user.data_expiracao = current_user.data_expiracao + timedelta(days=product.duration_days)
            else:
                current_user.data_expiracao = datetime.utcnow() + timedelta(days=product.duration_days)
            
            current_user.status_licenca = "ativa"
            payment_record.status = "completed"
            db.commit()
            
            print(f"🎉 Licença ativada até: {current_user.data_expiracao}")
        
        return {
            "success": True,
            "payment_id": payment_result["id"],
            "status": payment_result["status"],
            "status_detail": payment_result.get("status_detail"),
            "message": "Pagamento processado com sucesso"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Erro no pagamento seguro: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/test-payment/{plan_id}")
async def test_payment_activation(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint para testar ativação de pagamento (apenas para desenvolvimento)"""
    try:
        from mercadopago_integration import activate_user_license

        success, message = activate_user_license(current_user.id, plan_id)

        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
