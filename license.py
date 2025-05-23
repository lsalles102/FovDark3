from datetime import datetime
from sqlalchemy.orm import Session
from models import User, Payment


def verify_license(user: User) -> bool:
    """Verificar se a licença do usuário está válida"""
    if not user.data_expiracao:
        return False
    
    return user.data_expiracao > datetime.utcnow()


def create_payment_record(db: Session, user_id: int, valor: float, plano: str = None) -> Payment:
    """Criar registro de pagamento"""
    payment = Payment(
        user_id=user_id,
        valor=valor,
        plano=plano,
        status="completed"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return payment


def get_license_status(user: User) -> dict:
    """Obter status detalhado da licença"""
    if not user.data_expiracao:
        return {
            "status": "sem_licenca",
            "message": "Usuário não possui licença ativa",
            "expires_at": None,
            "days_remaining": 0
        }
    
    now = datetime.utcnow()
    
    if user.data_expiracao <= now:
        return {
            "status": "expirada",
            "message": "Licença expirada",
            "expires_at": user.data_expiracao.isoformat(),
            "days_remaining": 0
        }
    
    days_remaining = (user.data_expiracao - now).days
    
    if days_remaining <= 3:
        status = "expirando"
        message = f"Licença expira em {days_remaining} dias"
    elif days_remaining <= 7:
        status = "aviso"
        message = f"Licença expira em {days_remaining} dias"
    else:
        status = "ativa"
        message = "Licença ativa"
    
    return {
        "status": status,
        "message": message,
        "expires_at": user.data_expiracao.isoformat(),
        "days_remaining": days_remaining
    }
