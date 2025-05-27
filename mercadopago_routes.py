
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from database import get_db
from models import User, Payment
from auth import get_current_user
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
        
        return {
            "preference_id": preference["id"],
            "init_point": preference["init_point"],
            "sandbox_init_point": preference.get("sandbox_init_point")
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
