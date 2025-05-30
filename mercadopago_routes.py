from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from database import get_db
from models import User, Payment
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

@router.post("/create-checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Criar checkout no Mercado Pago"""
    try:
        print(f"🛒 Criando checkout para usuário: {current_user.email}")
        print(f"📦 Dados recebidos: {request}")

        # Validar se não é admin tentando comprar para si mesmo
        #if current_user.is_admin:
        #    raise HTTPException(
        #        status_code=400, 
        #        detail="Não é possível pagar para você mesmo."
        #    )

        # Buscar produto no banco de dados se product_id fornecido
        if request.product_id:
            from models import Product
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

        if not init_point and not sandbox_init_point:
            print("❌ Nenhuma URL de checkout encontrada na resposta do Mercado Pago")
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
        # Obter dados do webhook
        body = await request.body()

        # Log do webhook recebido
        print(f"🔔 Webhook recebido do Mercado Pago")
        print(f"📋 Headers: {dict(request.headers)}")

        # Tentar decodificar como JSON
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            # Se não for JSON válido, tentar como form data
            form_data = await request.form()
            data = dict(form_data)

        print(f"📊 Dados recebidos: {data}")

        # Verificar se é uma notificação de pagamento
        if data.get("type") == "payment":
            success, message = handle_payment_notification(data)

            if success:
                print(f"✅ Webhook processado: {message}")
                return {"status": "ok", "message": message}
            else:
                print(f"❌ Erro no webhook: {message}")
                return {"status": "error", "message": message}
        else:
            print(f"ℹ️ Tipo de notificação ignorado: {data.get('type', 'unknown')}")
            return {"status": "ok", "message": "Tipo de notificação não processado"}

    except Exception as e:
        print(f"💥 Erro crítico no webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

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