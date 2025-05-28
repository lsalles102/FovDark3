import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

from database import get_db, engine, Base
from models import User, Payment, Product, SiteSettings
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash, verify_password, decode_access_token
)
from mercadopago_routes import router as mercadopago_router
from license import verify_license, create_payment_record, get_license_status
from admin import get_admin_user
from email_utils import send_confirmation_email, send_recovery_email

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FovDark - Sistema de Vendas", version="1.0.0")
app.include_router(mercadopago_router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBearer()

class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/static") or request.url.path.startswith("/admin") or request.url.path.startswith("/api/admin"):
            return await call_next(request)

        try:
            from database import SessionLocal
            db = SessionLocal()
            maintenance_setting = db.query(SiteSettings).filter(
                SiteSettings.key == "maintenance_mode",
                SiteSettings.category == "system"
            ).first()
            if maintenance_setting and maintenance_setting.value == "true":
                return templates.TemplateResponse("maintenance.html", {"request": request}, status_code=503)
            db.close()
        except Exception:
            pass

        return await call_next(request)

app.add_middleware(MaintenanceMiddleware)

async def verify_token_middleware(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
    return payload

@app.post("/api/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senhas não coincidem")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já está em uso")

    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        senha_hash=hashed_password,
        data_expiracao=None,
        status_licenca="pendente",
        ip_registro=request.client.host
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        send_confirmation_email(email)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

    return {"message": "Usuário criado com sucesso", "user_id": new_user.id}

@app.post("/api/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user_check = db.query(User).filter(User.email.ilike(email.strip())).first()
        if not user_check:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

        user = authenticate_user(db, email.strip(), password)
        if not user:
            user_check.tentativas_login += 1
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

        user.tentativas_login = 0
        user.ultimo_login = datetime.utcnow()
        user.ip_ultimo_login = request.client.host
        db.commit()

        AUTHORIZED_ADMIN_EMAILS = ["admin@fovdark.com", "lsalles102@gmail.com"]
        user_email_lower = user.email.lower().strip()
        is_authorized_admin = user_email_lower in [email.lower() for email in AUTHORIZED_ADMIN_EMAILS]

        if is_authorized_admin:
            if not user.is_admin:
                user.is_admin = True
                db.commit()
        else:
            if user.is_admin:
                user.is_admin = False
                db.commit()

        access_token = create_access_token(data={"sub": user.email})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "is_admin": user.is_admin,
                "data_expiracao": user.data_expiracao.isoformat() if user.data_expiracao else None
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor durante o login")

@app.get("/api/admin/users")
async def get_all_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    status_licenca: Optional[str] = None,
    min_tentativas: Optional[int] = None,
    ip_filter: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    query = db.query(User)
    
    # Aplicar filtros
    if status_licenca:
        query = query.filter(User.status_licenca == status_licenca)
    
    if min_tentativas is not None:
        query = query.filter(User.tentativas_login >= min_tentativas)
    
    if ip_filter:
        query = query.filter(
            (User.ip_registro.like(f"%{ip_filter}%")) |
            (User.ip_ultimo_login.like(f"%{ip_filter}%"))
        )
    
    # Paginação
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "is_admin": user.is_admin,
                "data_expiracao": user.data_expiracao.isoformat() if user.data_expiracao else None,
                "status_licenca": user.status_licenca,
                "tentativas_login": user.tentativas_login,
                "ultimo_login": user.ultimo_login.isoformat() if user.ultimo_login else None,
                "ip_registro": user.ip_registro,
                "ip_ultimo_login": user.ip_ultimo_login,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ],
        "total": total,
        "offset": offset,
        "limit": limit
    }

@app.get("/api/admin/dashboard")
async def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Estatísticas gerais
    total_users = db.query(User).count()
    active_licenses = db.query(User).filter(
        User.data_expiracao.isnot(None),
        User.data_expiracao > datetime.utcnow()
    ).count()
    
    # Estatísticas por status de licença
    license_stats = db.query(
        User.status_licenca,
        db.func.count(User.id).label('count')
    ).group_by(User.status_licenca).all()
    
    # Usuários com tentativas de login suspeitas
    suspicious_logins = db.query(User).filter(User.tentativas_login >= 3).count()
    
    # Últimos logins (últimas 24h)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_logins = db.query(User).filter(
        User.ultimo_login >= last_24h
    ).count()
    
    # IPs mais comuns
    ip_stats = db.query(
        User.ip_ultimo_login,
        db.func.count(User.id).label('count')
    ).filter(
        User.ip_ultimo_login.isnot(None)
    ).group_by(User.ip_ultimo_login).order_by(
        db.func.count(User.id).desc()
    ).limit(10).all()
    
    # Registros por dia (últimos 30 dias)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_registrations = db.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(db.func.date(User.created_at)).all()
    
    return {
        "general_stats": {
            "total_users": total_users,
            "active_licenses": active_licenses,
            "suspicious_logins": suspicious_logins,
            "recent_logins_24h": recent_logins
        },
        "license_distribution": [
            {"status": status, "count": count}
            for status, count in license_stats
        ],
        "top_ips": [
            {"ip": ip, "count": count}
            for ip, count in ip_stats if ip
        ],
        "daily_registrations": [
            {"date": date.isoformat(), "count": count}
            for date, count in daily_registrations
        ]
    }

@app.get("/api/admin/user-activity")
async def get_user_activity(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    days: Optional[int] = 7
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Atividade de login por dia
    login_activity = db.query(
        db.func.date(User.ultimo_login).label('date'),
        db.func.count(User.id).label('logins')
    ).filter(
        User.ultimo_login >= start_date
    ).group_by(db.func.date(User.ultimo_login)).all()
    
    # Tentativas de login falhadas
    failed_attempts = db.query(
        User.email,
        User.tentativas_login,
        User.ip_ultimo_login
    ).filter(
        User.tentativas_login > 0
    ).order_by(User.tentativas_login.desc()).limit(20).all()
    
    return {
        "login_activity": [
            {"date": date.isoformat(), "logins": logins}
            for date, logins in login_activity
        ],
        "failed_attempts": [
            {
                "email": email,
                "attempts": attempts,
                "last_ip": ip
            }
            for email, attempts, ip in failed_attempts
        ]
    }

@app.get("/api/admin/security-report")
async def get_security_report(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Múltiplos IPs por usuário
    multi_ip_users = db.query(
        User.email,
        User.ip_registro,
        User.ip_ultimo_login
    ).filter(
        User.ip_registro != User.ip_ultimo_login,
        User.ip_registro.isnot(None),
        User.ip_ultimo_login.isnot(None)
    ).all()
    
    # Usuários sem login recente (30 dias)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    inactive_users = db.query(User).filter(
        (User.ultimo_login < thirty_days_ago) |
        (User.ultimo_login.is_(None))
    ).count()
    
    # IPs suspeitos (múltiplos usuários)
    suspicious_ips = db.query(
        User.ip_ultimo_login,
        db.func.count(User.id).label('user_count')
    ).filter(
        User.ip_ultimo_login.isnot(None)
    ).group_by(User.ip_ultimo_login).having(
        db.func.count(User.id) > 3
    ).order_by(db.func.count(User.id).desc()).all()
    
    return {
        "multi_ip_users": [
            {
                "email": email,
                "registration_ip": reg_ip,
                "last_login_ip": login_ip
            }
            for email, reg_ip, login_ip in multi_ip_users
        ],
        "inactive_users_count": inactive_users,
        "suspicious_ips": [
            {"ip": ip, "user_count": count}
            for ip, count in suspicious_ips
        ]
    }

# Rotas HTML
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/comprar", response_class=HTMLResponse)
async def comprar_page(request: Request):
    return templates.TemplateResponse("comprar.html", {"request": request})

@app.get("/painel", response_class=HTMLResponse)
async def painel_page(request: Request):
    return templates.TemplateResponse("painel.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/recover", response_class=HTMLResponse)
async def recover_page(request: Request):
    return templates.TemplateResponse("recover.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
