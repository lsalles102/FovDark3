import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User

# Configurações JWT
SECRET_KEY = os.getenv("SECRET_KEY", "darkfov-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuração bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gerar hash da senha"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autenticar usuário"""
    try:
        print(f"🔍 Buscando usuário no banco: {email}")
        user = db.query(User).filter(User.email.ilike(email.strip())).first()
        if not user:
            print(f"❌ Usuário não encontrado no banco: {email}")
            return None
        
        print(f"✅ Usuário encontrado no banco: {user.email}")
        print(f"🔐 Verificando senha...")
        
        password_valid = verify_password(password, user.senha_hash)
        print(f"🔐 Resultado da verificação da senha: {password_valid}")
        
        if not password_valid:
            print(f"❌ Senha incorreta para: {email}")
            return None
        
        print(f"✅ Autenticação bem-sucedida para: {email}")
        return user
    except Exception as e:
        print(f"💥 Erro na autenticação: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Criar token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obter usuário atual do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    # Lista de emails autorizados como admin (case-insensitive)
    AUTHORIZED_ADMIN_EMAILS = [
        "admin@fovdark.com",
        "lsalles102@gmail.com"
    ]

    # Verificar se o email está autorizado como admin (comparação case-insensitive)
    user_email_lower = user.email.lower().strip()
    is_authorized_admin = user_email_lower in [email.lower() for email in AUTHORIZED_ADMIN_EMAILS]
    
    if is_authorized_admin:
        # Garantir que usuários autorizados sejam admin
        if not user.is_admin:
            user.is_admin = True
            db.commit()
            print(f"👑 Usuário {user.email} promovido a admin")
    else:
        # Garantir que usuários não autorizados NÃO sejam admin
        if user.is_admin:
            user.is_admin = False
            db.commit()
            print(f"👤 Privilégios de admin removidos de {user.email}")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obter usuário ativo atual"""
    return current_user