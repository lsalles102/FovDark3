
import os
import stripe
from datetime import datetime, timedelta
from fastapi import HTTPException

# Configurar a chave da API do Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PLANOS = {
    "mensal": {
        "price_id": os.getenv("STRIPE_PRICE_MENSAL", "price_mensal"),
        "valor": 7990,  # R$ 79,90
        "dias": 30,
        "nome": "Plano Mensal",
        "moeda": "brl"
    },
    "trimestral": {
        "price_id": os.getenv("STRIPE_PRICE_TRIMESTRAL", "price_trimestral"), 
        "valor": 19990,  # R$ 199,90
        "dias": 90,
        "nome": "Plano Trimestral",
        "moeda": "brl"
    },
    "anual": {
        "price_id": os.getenv("STRIPE_PRICE_ANUAL", "price_anual"),
        "valor": 29990,  # R$ 299,90
        "dias": 365,
        "nome": "Plano Anual", 
        "moeda": "brl"
    }
}

async def criar_sessao_checkout(plano: str, user_email: str, success_url: str, cancel_url: str):
    """Criar sessão de checkout do Stripe"""
    if plano not in PLANOS:
        raise HTTPException(status_code=400, detail="Plano inválido")
        
    plano_info = PLANOS[plano]
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            line_items=[{
                'price': plano_info['price_id'],
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'plano': plano,
                'email': user_email
            },
            currency=plano_info['moeda'],
            locale='pt-BR',
            payment_method_types=['card'],
            billing_address_collection='required',
            customer_creation='always'
        )
        return checkout_session
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

async def processar_webhook(payload, sig_header, endpoint_secret):
    """Processar webhook do Stripe"""
    try:
        evento = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        return evento
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook inválido")

def calcular_data_expiracao(plano: str, data_atual_expiracao: datetime = None):
    """Calcular nova data de expiração"""
    if plano not in PLANOS:
        raise HTTPException(status_code=400, detail="Plano inválido")
        
    dias = PLANOS[plano]['dias']
    
    if data_atual_expiracao and data_atual_expiracao > datetime.utcnow():
        return data_atual_expiracao + timedelta(days=dias)
    else:
        return datetime.utcnow() + timedelta(days=dias)
