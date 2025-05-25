from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from stripe_integration import create_checkout_session, handle_payment_success
from auth import decode_access_token
import stripe
import os

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

    try:
        checkout_session = create_checkout_session(plano, user.id, user.email)
        if 'error' in checkout_session:
            raise HTTPException(status_code=400, detail=checkout_session['error'])
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook error")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        success, message = handle_payment_success(session)
        if not success:
            raise HTTPException(status_code=400, detail=message)

    return {"status": "success"}