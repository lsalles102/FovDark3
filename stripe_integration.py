
import os
import stripe
from datetime import datetime, timedelta
from models import User, Payment
from database import get_db

# Configuração da API do Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY não configurada. Configure a chave no Secrets.")

# Definição dos produtos
PRODUCTS = {
    'mensal': {
        'name': 'Plano Mensal',
        'price': 7990,  # R$ 79,90
        'days': 30,
        'currency': 'brl'
    },
    'trimestral': {
        'name': 'Plano Trimestral',
        'price': 19990,  # R$ 199,90
        'days': 90,
        'currency': 'brl'
    },
    'anual': {
        'name': 'Plano Anual',
        'price': 29990,  # R$ 299,90
        'days': 365,
        'currency': 'brl'
    }
}

def get_domain():
    """Obtém o domínio para redirecionamento"""
    return "https://fovdark.repl.co"

def create_checkout_session(plan_id, user_id, user_email):
    """Cria uma sessão de checkout no Stripe"""
    if plan_id not in PRODUCTS:
        raise ValueError(f"Plano {plan_id} não encontrado")
    
    product = PRODUCTS[plan_id]
    domain_url = get_domain()
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': product['currency'],
                    'product_data': {
                        'name': product['name'],
                        'description': f'DarkFov - {product["name"]} - {product["days"]} dias',
                    },
                    'unit_amount': product['price'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + '/sucesso',
            cancel_url=domain_url + '/cancelado',
            client_reference_id=str(user_id),
            metadata={
                'plan_id': plan_id,
                'days': str(product['days']),
                'user_id': str(user_id)
            }
        )
        return checkout_session
    except Exception as e:
        return {'error': str(e)}

def handle_payment_success(session):
    """Processa um pagamento bem-sucedido"""
    try:
        db = next(get_db())
        user_id = int(session.metadata['user_id'])
        plan_id = session.metadata['plan_id']
        
        # Verificar se o usuário existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Usuário não encontrado"
        
        # Criar registro de pagamento
        payment = Payment(
            user_id=user_id,
            valor=PRODUCTS[plan_id]['price'] / 100,  # Converte centavos para reais
            status='completed',
            plano=plan_id,
            gateway_id=session.id
        )
        db.add(payment)
        
        # Atualizar licença
        if user.data_expiracao and user.data_expiracao > datetime.utcnow():
            # Estender licença existente
            user.data_expiracao = user.data_expiracao + timedelta(days=PRODUCTS[plan_id]['days'])
        else:
            # Nova licença
            user.data_expiracao = datetime.utcnow() + timedelta(days=PRODUCTS[plan_id]['days'])
        
        db.commit()
        return True, "Pagamento processado com sucesso"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def get_plan_details(plan_id):
    """Retorna os detalhes de um plano"""
    if plan_id in PRODUCTS:
        return PRODUCTS[plan_id]
    return None
