import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter()

@router.post("/criar-checkout")
async def criar_checkout():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': 9900,
                    'product_data': {
                        'name': 'Licença DarkFov',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://web-production-fa022.up.railway.app/sucesso',
            cancel_url='https://web-production-fa022.up.railway.app/cancelado',
        )
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Webhook signature verification failed")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"✅ Pagamento recebido! Sessão: {session['id']}")

    return JSONResponse(content={"status": "sucesso"})
