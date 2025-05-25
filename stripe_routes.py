
import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models import User, Payment
from email_utils import send_recovery_email

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

PLANOS = {
    "mensal": {
        "price_id": "price_XXXXX",  # Substitua pelo seu ID real do Stripe
        "dias": 30,
        "valor": 9900
    },
    "trimestral": {
        "price_id": "price_YYYYY",  # Substitua pelo seu ID real do Stripe
        "dias": 90,
        "valor": 24900
    },
    "anual": {
        "price_id": "price_ZZZZZ",  # Substitua pelo seu ID real do Stripe
        "dias": 365,
        "valor": 89900
    }
}

@router.post("/criar-checkout")
async def criar_checkout(plano: str, user_id: int, db: Session = Depends(get_db)):
    if plano not in PLANOS:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    plano_info = PLANOS[plano]
    user = db.query(User).filter(User.id == user_id).first()
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': plano_info['price_id'],
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://darkfov.repl.co/sucesso',
            cancel_url='https://darkfov.repl.co/cancelado',
            metadata={
                'user_id': user_id,
                'plano': plano
            }
        )
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook error")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Processar pagamento
        user_id = int(session['metadata']['user_id'])
        plano = session['metadata']['plano']
        plano_info = PLANOS[plano]
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(status_code=404, content={"error": "Usuário não encontrado"})
        
        # Atualizar licença
        if user.data_expiracao and user.data_expiracao > datetime.utcnow():
            nova_expiracao = user.data_expiracao + timedelta(days=plano_info['dias'])
        else:
            nova_expiracao = datetime.utcnow() + timedelta(days=plano_info['dias'])
        
        user.data_expiracao = nova_expiracao
        
        # Registrar pagamento
        payment = Payment(
            user_id=user_id,
            valor=plano_info['valor'] / 100,  # Converter centavos para reais
            status='completed',
            plano=plano,
            gateway_id=session.id
        )
        
        db.add(payment)
        db.commit()
        
        print(f"✅ Pagamento processado! User ID: {user_id}, Plano: {plano}")
    
    return JSONResponse(content={"status": "success"})
