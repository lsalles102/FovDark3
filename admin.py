from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from auth import get_current_user
from database import get_db


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verificar se o usuário é administrador"""
    # Verificação rigorosa de administrador
    if not current_user or not hasattr(current_user, 'is_admin') or current_user.is_admin != True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Privilégios de administrador necessários."
        )

    # Lista de emails de administradores permitidos (configuração adicional de segurança)
    ADMIN_EMAILS = [
        "admin@fovdark.com",
        "lsalles102@gmail.com"  # Adicione emails de admin aqui
    ]

    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Email não autorizado para administração."
        )

    return current_user


def create_admin_user(db: Session, email: str, password_hash: str) -> User:
    """Criar usuário administrador"""
    admin_user = User(
        email=email,
        senha_hash=password_hash,
        is_admin=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return admin_user


def get_user_statistics(db: Session) -> dict:
    """Obter estatísticas de usuários"""
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    active_licenses = db.query(User).filter(
        User.data_expiracao.isnot(None),
        User.data_expiracao > db.func.now()
    ).count()

    return {
        "total_users": total_users,
        "admin_users": admin_users,
        "active_licenses": active_licenses,
        "regular_users": total_users - admin_users
    }