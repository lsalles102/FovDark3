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
            "days_remaining": 0,
            "hours_remaining": 0,
            "is_valid": False,
            "can_download": False
        }
    
    now = datetime.utcnow()
    
    if user.data_expiracao <= now:
        return {
            "status": "expirada",
            "message": "Licença expirada",
            "expires_at": user.data_expiracao.isoformat(),
            "days_remaining": 0,
            "hours_remaining": 0,
            "is_valid": False,
            "can_download": False
        }
    
    time_remaining = user.data_expiracao - now
    days_remaining = time_remaining.days
    hours_remaining = time_remaining.seconds // 3600
    
    if days_remaining <= 1 and hours_remaining <= 24:
        status = "critico"
        if days_remaining == 0:
            message = f"Licença expira em {hours_remaining} horas"
        else:
            message = f"Licença expira em {days_remaining} dia e {hours_remaining} horas"
    elif days_remaining <= 3:
        status = "expirando"
        message = f"Licença expira em {days_remaining} dias"
    elif days_remaining <= 7:
        status = "aviso"
        message = f"Licença expira em {days_remaining} dias"
    else:
        status = "ativa"
        message = f"Licença ativa por mais {days_remaining} dias"
    
    return {
        "status": status,
        "message": message,
        "expires_at": user.data_expiracao.isoformat(),
        "days_remaining": days_remaining,
        "hours_remaining": hours_remaining,
        "is_valid": True,
        "can_download": True
    }
