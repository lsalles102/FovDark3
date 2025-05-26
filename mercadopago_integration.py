import os
import mercadopago
from datetime import datetime, timedelta
from models import User, Payment
from database import get_db

# Inicializar SDK do MercadoPago
MERCADOPAGO_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
if MERCADOPAGO_TOKEN:
    mp = mercadopago.SDK(MERCADOPAGO_TOKEN)
else:
    print("⚠️ MercadoPago token não configurado - Pagamentos desabilitados")
    mp = None

# Remover a validação que quebra a aplicação - será tratada nos endpoints

# Definição dos produtos
PRODUCTS = {
    'mensal': {
        'name': 'Plano Mensal',
        'price': 79.90,
        'days': 30,
        'currency': 'BRL'
    },
    'trimestral': {
        'name': 'Plano Trimestral',
        'price': 199.90,
        'days': 90,
        'currency': 'BRL'
    },
    'anual': {
        'name': 'Plano Anual',
        'price': 299.90,
        'days': 365,
        'currency': 'BRL'
    }
}

def get_domain():
    """Obtém o domínio para redirecionamento"""
    return "https://fovdark.repl.co"

def create_payment_preference(plan_id, user_id, user_email):
    """Cria uma preferência de pagamento no Mercado Pago"""
    if not mp:
        return {"error": "Pagamentos temporariamente indisponíveis"}
    if plan_id not in PRODUCTS:
        raise ValueError(f"Plano {plan_id} não encontrado")

    product = PRODUCTS[plan_id]
    domain_url = get_domain()

    try:
        preference_data = {
            "items": [
                {
                    "title": product['name'],
                    "description": f'DarkFov - {product["name"]} - {product["days"]} dias',
                    "quantity": 1,
                    "currency_id": product['currency'],
                    "unit_price": product['price']
                }
            ],
            "payer": {
                "email": user_email
            },
            "back_urls": {
                "success": domain_url + "/sucesso",
                "failure": domain_url + "/cancelado",
                "pending": domain_url + "/pendente"
            },
            "auto_return": "approved",
            "external_reference": str(user_id),
            "metadata": {
                "plan_id": plan_id,
                "days": str(product['days']),
                "user_id": str(user_id)
            },
            "payment_methods": {
                "excluded_payment_types": [],
                "installments": 12
            },
            "notification_url": domain_url + "/api/webhook/mercadopago"
        }

        preference_response = mp.preference().create(preference_data)

        if preference_response["status"] == 201:
            return preference_response["response"]
        else:
            return {'error': preference_response["response"]}

    except Exception as e:
        return {'error': str(e)}

def handle_payment_notification(payment_data):
    """Processa notificação de pagamento do Mercado Pago"""
    try:
        # Obter dados do pagamento
        payment_id = payment_data.get("data", {}).get("id")
        if not payment_id:
            return False, "ID do pagamento não encontrado"

        # Buscar informações do pagamento
        payment_info = mp.payment().get(payment_id)

        if payment_info["status"] != 200:
            return False, "Erro ao buscar informações do pagamento"

        payment_details = payment_info["response"]

        # Verificar se o pagamento foi aprovado
        if payment_details["status"] != "approved":
            return True, f"Pagamento com status: {payment_details['status']}"

        # Obter dados do usuário
        external_reference = payment_details.get("external_reference")
        if not external_reference:
            return False, "Referência externa não encontrada"

        user_id = int(external_reference)

        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Usuário não encontrado"

        # Verificar se o pagamento já foi processado
        existing_payment = db.query(Payment).filter(
            Payment.gateway_id == str(payment_id)
        ).first()

        if existing_payment:
            return True, "Pagamento já processado"

        # Obter metadados da preferência original
        preference_id = payment_details.get("preference_id")
        if preference_id:
            preference_info = mp.preference().get(preference_id)
            if preference_info["status"] == 200:
                metadata = preference_info["response"].get("metadata", {})
                plan_id = metadata.get("plan_id")
                days = int(metadata.get("days", 30))
            else:
                # Fallback para plano mensal se não conseguir obter metadata
                plan_id = "mensal"
                days = 30
        else:
            plan_id = "mensal"
            days = 30

        # Criar registro de pagamento
        payment = Payment(
            user_id=user_id,
            valor=payment_details["transaction_amount"],
            status='completed',
            plano=plan_id,
            gateway_id=str(payment_id)
        )
        db.add(payment)

        # Atualizar licença do usuário
        if user.data_expiracao and user.data_expiracao > datetime.utcnow():
            # Estender licença existente
            user.data_expiracao = user.data_expiracao + timedelta(days=days)
        else:
            # Nova licença
            user.data_expiracao = datetime.utcnow() + timedelta(days=days)

        db.commit()
        return True, "Pagamento processado com sucesso"

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return False, str(e)

def get_plan_details(plan_id):
    """Retorna os detalhes de um plano"""
    if plan_id in PRODUCTS:
        return PRODUCTS[plan_id]
    return None