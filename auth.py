import os
from datetime import datetime, timedelta
from typing import Optional
import logging
from functools import wraps
import time

# Rate limiting simples
login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 300  # 5 minutos

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
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutos para melhor segurança

# Configuração bcrypt com versão específica para evitar erro de compatibilidade
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
except Exception as e:
    print(f"⚠️ Erro na configuração bcrypt: {e}")
    # Fallback para configuração mais básica
    pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

security = HTTPBearer()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def check_rate_limit(email: str) -> bool:
    """Verifica se o email não excedeu o limite de tentativas"""
    current_time = time.time()

    if email in login_attempts:
        attempts, last_attempt = login_attempts[email]

        # Reset counter se passou o tempo de bloqueio
        if current_time - last_attempt > BLOCK_TIME:
            login_attempts[email] = (1, current_time)
            return True

        # Bloquear se excedeu tentativas
        if attempts >= MAX_ATTEMPTS:
            return False

        # Incrementar tentativas
        login_attempts[email] = (attempts + 1, current_time)
    else:
        login_attempts[email] = (1, current_time)

    return True

def reset_rate_limit(email: str):
    """Reset contador de tentativas após login bem-sucedido"""
    if email in login_attempts:
        del login_attempts[email]


def get_password_hash(password: str) -> str:
    """Gerar hash da senha com tratamento de erros"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"❌ Erro ao gerar hash: {e}")
        # Fallback para bcrypt direto
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autenticar usuário"""
    try:
        # Log sem expor email completo
        email_masked = email[:3] + "***" + email[email.find('@'):]
        print(f"🔍 Tentativa de autenticação para: {email_masked}")

        # Verificar rate limit
        if not check_rate_limit(email):
            print(f"🚫 Muitas tentativas de login para: {email_masked}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de login. Tente novamente mais tarde."
            )

        user = db.query(User).filter(User.email.ilike(email.strip())).first()
        if not user:
            print(f"❌ Usuário não encontrado")
            return None

        # Verificar se há muitas tentativas de login
        if user.tentativas_login >= 5:
            print(f"🚫 Conta bloqueada por muitas tentativas")
            return None

        print(f"✅ Usuário encontrado")

        password_valid = verify_password(password, user.senha_hash)

        if not password_valid:
            print(f"❌ Falha na autenticação")
            return None

        reset_rate_limit(email)  # Resetar tentativas após sucesso
        print(f"✅ Autenticação bem-sucedida")
        return user
    except HTTPException as http_ex:
        raise http_ex  # Re-raise para que o handler superior capture
    except Exception as e:
        print(f"💥 Erro na autenticação: erro interno")
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