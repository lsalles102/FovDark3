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
# Configurações temporárias do Mercado Pago
PRODUCTS = {
    "mensal": {
        "name": "Plano Mensal",
        "price": 79.90,
        "duration_days": 30
    },
    "trimestral": {
        "name": "Plano Trimestral", 
        "price": 199.90,
        "duration_days": 90
    },
    "anual": {
        "name": "Plano Anual",
        "price": 299.90,
        "duration_days": 365
    }
}

def create_payment_preference(plan_id, user_id, user_email):
    # Simulação temporária - em produção usar SDK do Mercado Pago
    return {
        "id": f"fake_pref_{user_id}_{plan_id}",
        "init_point": f"/sucesso?plan={plan_id}",
        "sandbox_init_point": f"/sucesso?plan={plan_id}"
    }

def handle_payment_notification(data):
    return True, "Payment processed"

def get_plan_details(plan_id):
    return PRODUCTS.get(plan_id)

router = APIRouter()

@router.post("/mercadopago/create-preference")
async def create_preference(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        plan_id = data.get("plan_id")

        if not plan_id or plan_id not in PRODUCTS:
            raise HTTPException(status_code=400, detail="Plano inválido")

        # Criar preferência no Mercado Pago
        preference = create_payment_preference(
            plan_id=plan_id,
            user_id=current_user.id,
            user_email=current_user.email
        )

        if "error" in preference:
            raise HTTPException(status_code=400, detail=preference["error"])

        # Criar registro de pagamento pendente
        new_payment = Payment(
            user_id=current_user.id,
            valor=PRODUCTS[plan_id]["price"],
            plano=plan_id,
            status="pendente",
            gateway_id=preference["id"]
        )
        db.add(new_payment)
        db.commit()

        return {
            "success": True,
            "preference_id": preference["id"],
            "init_point": preference["init_point"],
            "sandbox_init_point": preference.get("sandbox_init_point"),
            "message": "Preferência criada com sucesso"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        # Obter dados do webhook
        body = await request.body()
        data = json.loads(body)

        # Processar notificação
        success, message = handle_payment_notification(data)

        if success:
            return {"status": "ok", "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/payment/status/{payment_id}")
async def check_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
            "status": payment.status,
            "amount": payment.valor,
            "plan": payment.plano,
            "date": payment.data_pagamento.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def get_available_plans():
    """Retorna os planos disponíveis"""
    return PRODUCTS

class CheckoutRequest(BaseModel):
    plano: str
    product_id: Optional[int] = None

@router.post("/criar-checkout")
async def criar_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from models import Product
    
    # Buscar produto no banco de dados
    if request.product_id:
        produto_db = db.query(Product).filter(
            Product.id == request.product_id,
            Product.is_active == True
        ).first()
        
        if not produto_db:
            raise HTTPException(status_code=404, detail="Produto não encontrado ou inativo")

        produto = {
            "id": produto_db.id,
            "preco": produto_db.price,
            "duracao": produto_db.duration_days,
            "nome": produto_db.name
        }
    else:
        # Fallback para compatibilidade com planos antigos
        produtos_legacy = {
            "basico": {"preco": 19.90, "duracao": 7, "nome": "Plano Básico"},
            "premium": {"preco": 49.90, "duracao": 30, "nome": "Plano Premium"},
            "vip": {"preco": 89.90, "duracao": 60, "nome": "Plano VIP"}
        }

        if request.plano in produtos_legacy:
            legacy_produto = produtos_legacy[request.plano]
            produto = {
                "id": None,
                "preco": legacy_produto["preco"],
                "duracao": legacy_produto["duracao"],
                "nome": legacy_produto["nome"]
            }
        else:
            raise HTTPException(status_code=400, detail="Produto não encontrado")

    # Criar preferência no Mercado Pago
    preference_data = {
        "items": [
            {
                "title": produto["nome"],
                "quantity": 1,
                "unit_price": float(produto["preco"]),
                "description": f"Acesso por {produto['duracao']} dias"
            }
        ],
        "payer": {
            "email": current_user.email
        },
        "back_urls": {
            "success": "/sucesso",
            "failure": "/falha", 
            "pending": "/pendente"
        },
        "auto_return": "approved",
        "external_reference": f"user_{current_user.id}_product_{produto.get('id', 'legacy')}",
        "notification_url": "/webhook/mercadopago"
    }

    # Simulação de resposta do Mercado Pago - em produção usar SDK real
    import uuid
    preference_id = f"fake_pref_{uuid.uuid4().hex[:8]}"
    preference_response = {
        "id": preference_id,
        "init_point": f"https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id={preference_id}",
        "sandbox_init_point": f"https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id={preference_id}"
    }

    # Registrar pagamento no banco
    pagamento = Payment(
        user_id=current_user.id,
        product_id=produto.get("id"),
        valor=produto["preco"],
        plano=produto["nome"],
        gateway_id=preference_response["id"],
        status="pending"
    )

    db.add(pagamento)
    db.commit()
    db.refresh(pagamento)

    return {
        "success": True,
        "message": "Checkout criado com sucesso",
        "preference_id": preference_response["id"],
        "init_point": preference_response["init_point"],
        "sandbox_init_point": preference_response["sandbox_init_point"]
    }