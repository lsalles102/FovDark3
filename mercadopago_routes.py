from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from mercadopago_integration import create_payment_preference, handle_payment_notification
from auth import decode_access_token
import json
import os  # Import the os module

router = APIRouter()

@router.post("/criar-preferencia")
async def criar_preferencia(request: Request, db: Session = Depends(get_db)):
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
        preference = create_payment_preference(plano, user.id, user.email)
        if 'error' in preference:
            raise HTTPException(status_code=400, detail=preference['error'])

        return {
            "preference_id": preference.get("id"),
            "init_point": preference.get("init_point"),
            "sandbox_init_point": preference.get("sandbox_init_point")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request):
    try:
        # Verificar se o MercadoPago está configurado
        if not os.getenv("MERCADOPAGO_ACCESS_TOKEN"):
            return {"status": "disabled", "message": "MercadoPago não configurado"}

        # Verificar se é uma notificação de pagamento
        content_type = request.headers.get('content-type', '')

        if 'application/json' in content_type:
            body = await request.json()
        else:
            # Mercado Pago pode enviar como form data
            form_data = await request.form()
            body = {
                "action": form_data.get("action"),
                "api_version": form_data.get("api_version"),
                "data": {
                    "id": form_data.get("data.id")
                },
                "date_created": form_data.get("date_created"),
                "id": form_data.get("id"),
                "live_mode": form_data.get("live_mode"),
                "type": form_data.get("type"),
                "user_id": form_data.get("user_id")
            }

        # Processar apenas notificações de pagamento
        if body.get("type") == "payment":
            success, message = handle_payment_notification(body)
            if not success:
                print(f"Erro ao processar webhook: {message}")
                # Retorna 200 mesmo em erro para evitar reenvios desnecessários
                return {"status": "error", "message": message}

        return {"status": "success"}

    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return {"status": "error", "message": str(e)}