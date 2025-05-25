
import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from auth import decode_access_token
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User
from stripe_integration import create_checkout_session, process_webhook_payment

router = APIRouter()
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/criar-checkout")
async def criar_checkout(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    plano = body.get('plano')
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Token não fornecido")
        
    token = auth_header.split(' ')[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    email = payload.get('sub')
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    checkout_session = create_checkout_session(user, plano)
    return {"id": checkout_session.id}

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
        payment = process_webhook_payment(session, db)
        print(f"✅ Pagamento processado! User ID: {payment.user_id}, Plano: {payment.plano}")
    
    return JSONResponse(content={"status": "success"})
