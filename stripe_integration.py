
import os
import stripe
from datetime import datetime, timedelta
from fastapi import HTTPException
from models import User, Payment
from sqlalchemy.orm import Session

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLANOS = {
    "mensal": {
        "price_id": os.getenv("STRIPE_PRICE_MENSAL", "price_XXXXX"),
        "dias": 30,
        "valor": 2990,  # R$ 29,90
        "currency": "brl"
    },
    "trimestral": {
        "price_id": os.getenv("STRIPE_PRICE_TRIMESTRAL", "price_YYYYY"),
        "dias": 90,
        "valor": 7990,  # R$ 79,90
        "currency": "brl"
    },
    "anual": {
        "price_id": os.getenv("STRIPE_PRICE_ANUAL", "price_ZZZZZ"),
        "dias": 365,
        "valor": 29990,  # R$ 299,90
        "currency": "brl"
    }
}

def create_checkout_session(user: User, plano: str):
    if plano not in PLANOS:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    plano_info = PLANOS[plano]
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': plano_info['price_id'],
                'quantity': 1,
            }],
            mode='payment',
            currency=plano_info['currency'],
            locale='pt-BR',
            success_url='https://fovdark.repl.co/sucesso',
            cancel_url='https://fovdark.repl.co/cancelado',
            metadata={
                'user_id': user.id,
                'plano': plano
            }
        )
        return checkout_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_webhook_payment(session: dict, db: Session):
    user_id = int(session['metadata']['user_id'])
    plano = session['metadata']['plano']
    plano_info = PLANOS[plano]
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
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
        gateway_id=session['id']
    )
    
    db.add(payment)
    db.commit()
    
    return payment
