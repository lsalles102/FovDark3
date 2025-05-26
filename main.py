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
from license import verify_license, create_payment_record
from admin import get_admin_user
from email_utils import send_confirmation_email, send_recovery_email

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FovDark - Sistema de Vendas", version="1.0.0")
app.include_router(mercadopago_router, prefix="/api")

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBearer()


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Verificar se o modo manutenção está ativo
        if request.url.path.startswith("/static") or request.url.path.startswith("/admin") or request.url.path.startswith("/api/admin"):
            # Permitir acesso a arquivos estáticos e painel admin
            response = await call_next(request)
            return response
        
        # Verificar configuração de manutenção no banco
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
            pass  # Se houver erro no banco, continua normalmente
        
        response = await call_next(request)
        return response


# Adicionar middleware
app.add_middleware(MaintenanceMiddleware)


# Middleware para verificar token em rotas protegidas
async def verify_token_middleware(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    return payload


# Rota principal
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Página de login
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Página de registro
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/recover-password", response_class=HTMLResponse)
async def recover_password_page(request: Request):
    return templates.TemplateResponse("recover.html", {"request": request})

@app.post("/api/recover-password")
async def recover_password(email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email não encontrado")
    
    # Gerar token de recuperação
    recovery_token = create_access_token(
        data={"sub": user.email, "type": "recovery"},
        expires_delta=timedelta(hours=1)
    )
    
    # Enviar email
    try:
        send_recovery_email(email, recovery_token)
        return {"message": "Email de recuperação enviado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao enviar email")

@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/api/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "recovery":
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    user.senha_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Senha alterada com sucesso"}


# Página de compra
@app.get("/comprar", response_class=HTMLResponse)
async def comprar_page(request: Request):
    return templates.TemplateResponse("comprar.html", {"request": request})


# Painel do usuário
@app.get("/painel", response_class=HTMLResponse)
async def painel_page(request: Request):
    return templates.TemplateResponse("painel.html", {"request": request})


# Painel administrativo
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Páginas de retorno do Mercado Pago
@app.get("/sucesso", response_class=HTMLResponse)
async def pagamento_sucesso(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/cancelado", response_class=HTMLResponse)
async def pagamento_cancelado(request: Request):
    return templates.TemplateResponse("cancelled.html", {"request": request})

@app.get("/pendente", response_class=HTMLResponse)
async def pagamento_pendente(request: Request):
    return templates.TemplateResponse("pending.html", {"request": request})


# API Endpoints

# Registro de usuário
@app.post("/api/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senhas não coincidem"
        )
    
    # Verificar se usuário já existe
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Criar novo usuário
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        senha_hash=hashed_password,
        data_expiracao=None  # Sem licença inicialmente
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Enviar email de confirmação
    try:
        send_confirmation_email(email)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
    
    return {"message": "Usuário criado com sucesso", "user_id": new_user.id}


# Login
@app.post("/api/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
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


# Verificar licença
@app.get("/api/license/check")
async def check_license(
    current_user: User = Depends(get_current_user)
):
    is_valid = verify_license(current_user)
    return {
        "valid": is_valid,
        "email": current_user.email,
        "data_expiracao": current_user.data_expiracao.isoformat() if current_user.data_expiracao else None
    }


# Processar compra
@app.post("/api/purchase")
async def process_purchase(
    plano: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Definir preços e durações
    planos = {
        "mensal": {"preco": 29.90, "dias": 30},
        "trimestral": {"preco": 79.90, "dias": 90},
        "anual": {"preco": 299.90, "dias": 365}
    }
    
    if plano not in planos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano inválido"
        )
    
    plano_info = planos[plano]
    
    # Simular processamento de pagamento (em produção, integrar com gateway)
    # Aqui você integraria com Mercado Pago, PagSeguro, etc.
    
    # Criar registro de pagamento
    payment = create_payment_record(
        db, current_user.id, plano_info["preco"]
    )
    
    # Atualizar data de expiração do usuário
    if current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow():
        # Estender licença existente
        new_expiration = current_user.data_expiracao + timedelta(days=plano_info["dias"])
    else:
        # Nova licença
        new_expiration = datetime.utcnow() + timedelta(days=plano_info["dias"])
    
    current_user.data_expiracao = new_expiration
    db.commit()
    
    return {
        "message": "Compra processada com sucesso",
        "payment_id": payment.id,
        "nova_expiracao": new_expiration.isoformat()
    }


# Download do script (protegido)
@app.get("/api/download/script")
async def download_script(
    current_user: User = Depends(get_current_user)
):
    if not verify_license(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Licença expirada ou inexistente"
        )
    
    # Em produção, retornaria o arquivo real
    # Aqui vamos simular um arquivo
    script_content = f"""
# DarkFov Aim Assist Script
# Licenciado para: {current_user.email}
# Válido até: {current_user.data_expiracao}

import os
import sys

def main():
    print("DarkFov Aim Assist carregado com sucesso!")
    print(f"Usuário: {current_user.email}")
    print("Status: Licença ativa")
    
    # Aqui seria implementada a lógica do aim assist
    # IMPORTANTE: Este é apenas um exemplo educacional
    
if __name__ == "__main__":
    main()
"""
    
    # Criar arquivo temporário
    filename = f"darkfov_loader_{current_user.id}.py"
    with open(filename, "w") as f:
        f.write(script_content)
    
    return FileResponse(
        filename,
        media_type="application/octet-stream",
        filename="darkfov_loader.py"
    )


# Download do executável (protegido) - Para o loader
@app.get("/api/download/executable")
async def download_executable(
    current_user: User = Depends(get_current_user)
):
    if not verify_license(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Licença expirada ou inexistente"
        )
    
    # Verificar se o arquivo existe
    executable_path = "attached_assets/Script_Dark.exe"
    if not os.path.exists(executable_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Executável não encontrado"
        )
    
    return FileResponse(
        executable_path,
        media_type="application/octet-stream",
        filename="Script_Dark.exe"
    )


# Endpoints administrativos - Usuários
@app.get("/api/admin/users")
async def get_all_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "data_expiracao": user.data_expiracao.isoformat() if user.data_expiracao else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]


# Endpoints administrativos - Produtos
@app.get("/api/admin/products")
async def get_all_products(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    products = db.query(Product).all()
    return [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "duration_days": product.duration_days,
            "image_url": product.image_url,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "features": product.features,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        }
        for product in products
    ]


@app.post("/api/admin/products")
async def create_product(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    duration_days: int = Form(...),
    image_url: str = Form(""),
    features: str = Form(""),
    is_featured: bool = Form(False),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    new_product = Product(
        name=name,
        description=description,
        price=price,
        duration_days=duration_days,
        image_url=image_url,
        features=features,
        is_featured=is_featured,
        is_active=True
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {"message": "Produto criado com sucesso", "product_id": new_product.id}


@app.put("/api/admin/products/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    duration_days: int = Form(...),
    image_url: str = Form(""),
    features: str = Form(""),
    is_active: bool = Form(True),
    is_featured: bool = Form(False),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    product.name = name
    product.description = description
    product.price = price
    product.duration_days = duration_days
    product.image_url = image_url
    product.features = features
    product.is_active = is_active
    product.is_featured = is_featured
    
    db.commit()
    
    return {"message": "Produto atualizado com sucesso"}


@app.delete("/api/admin/products/{product_id}")
async def delete_product(
    product_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    db.delete(product)
    db.commit()
    
    return {"message": "Produto deletado com sucesso"}


# Endpoint público para listar produtos ativos
@app.get("/api/products")
async def get_active_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).all()
    return [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "duration_days": product.duration_days,
            "image_url": product.image_url,
            "is_featured": product.is_featured,
            "features": product.features
        }
        for product in products
    ]


@app.get("/api/admin/payments")
async def get_all_payments(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).all()
    return [
        {
            "id": payment.id,
            "user_id": payment.user_id,
            "valor": payment.valor,
            "data_pagamento": payment.data_pagamento.isoformat(),
            "status": payment.status
        }
        for payment in payments
    ]


@app.post("/api/admin/users/{user_id}/license")
async def update_user_license(
    user_id: int,
    dias: int = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if dias > 0:
        user.data_expiracao = datetime.utcnow() + timedelta(days=dias)
    else:
        user.data_expiracao = None
    
    db.commit()
    
    return {"message": "Licença atualizada com sucesso"}


@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível deletar administradores"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuário deletado com sucesso"}


# Endpoints para configurações do site
@app.get("/api/admin/settings")
async def get_site_settings(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    settings = db.query(SiteSettings).all()
    settings_dict = {}
    for setting in settings:
        if setting.category not in settings_dict:
            settings_dict[setting.category] = {}
        settings_dict[setting.category][setting.key] = setting.value
    return settings_dict


@app.post("/api/admin/settings")
async def update_site_settings(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        settings_data = await request.json()
        
        for category, settings in settings_data.items():
            for key, value in settings.items():
                # Buscar configuração existente
                setting = db.query(SiteSettings).filter(
                    SiteSettings.key == key,
                    SiteSettings.category == category
                ).first()
                
                if setting:
                    setting.value = str(value)
                    setting.updated_at = datetime.utcnow()
                else:
                    new_setting = SiteSettings(
                        key=key,
                        value=str(value),
                        category=category
                    )
                    db.add(new_setting)
        
        db.commit()
        return {"message": "Configurações atualizadas com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar configurações: {str(e)}"
        )


@app.post("/api/admin/settings/general")
async def save_general_settings(
    site_name: str = Form("DarkFov"),
    site_url: str = Form(""),
    support_email: str = Form(""),
    site_description: str = Form(""),
    mp_token: str = Form(""),
    smtp_host: str = Form(""),
    smtp_port: int = Form(587),
    smtp_email: str = Form(""),
    smtp_password: str = Form(""),
    enable_captcha: bool = Form(False),
    enable_two_factor: bool = Form(False),
    enable_email_verification: bool = Form(False),
    min_password_length: int = Form(8),
    main_download_url: str = Form(""),
    current_version: str = Form("1.0.0"),
    enable_download_auth: bool = Form(True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        # Configurações gerais
        general_settings = {
            "site_name": site_name,
            "site_url": site_url,
            "support_email": support_email,
            "site_description": site_description,
            "current_version": current_version
        }
        
        # Configurações de API
        api_settings = {
            "mp_token": mp_token,
            "smtp_host": smtp_host,
            "smtp_port": str(smtp_port),
            "smtp_email": smtp_email,
            "smtp_password": smtp_password
        }
        
        # Configurações de segurança
        security_settings = {
            "enable_captcha": str(enable_captcha),
            "enable_two_factor": str(enable_two_factor),
            "enable_email_verification": str(enable_email_verification),
            "min_password_length": str(min_password_length)
        }
        
        # Configurações de download
        download_settings = {
            "main_download_url": main_download_url,
            "enable_download_auth": str(enable_download_auth)
        }
        
        # Salvar todas as configurações
        all_settings = {
            "general": general_settings,
            "api": api_settings,
            "security": security_settings,
            "downloads": download_settings
        }
        
        for category, settings in all_settings.items():
            for key, value in settings.items():
                setting = db.query(SiteSettings).filter(
                    SiteSettings.key == key,
                    SiteSettings.category == category
                ).first()
                
                if setting:
                    setting.value = value
                    setting.updated_at = datetime.utcnow()
                else:
                    new_setting = SiteSettings(
                        key=key,
                        value=value,
                        category=category
                    )
                    db.add(new_setting)
        
        db.commit()
        return {"message": "Configurações gerais salvas com sucesso"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar configurações: {str(e)}"
        )


@app.post("/api/admin/maintenance")
async def toggle_maintenance_mode(
    enabled: bool = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Buscar configuração de manutenção
    maintenance_setting = db.query(SiteSettings).filter(
        SiteSettings.key == "maintenance_mode",
        SiteSettings.category == "system"
    ).first()
    
    if maintenance_setting:
        maintenance_setting.value = "true" if enabled else "false"
        maintenance_setting.updated_at = datetime.utcnow()
    else:
        new_setting = SiteSettings(
            key="maintenance_mode",
            value="true" if enabled else "false",
            category="system"
        )
        db.add(new_setting)
    
    db.commit()
    
    status_text = "ativado" if enabled else "desativado"
    return {"message": f"Modo manutenção {status_text} com sucesso", "enabled": enabled}


@app.get("/api/admin/maintenance/status")
async def get_maintenance_status(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    maintenance_setting = db.query(SiteSettings).filter(
        SiteSettings.key == "maintenance_mode",
        SiteSettings.category == "system"
    ).first()
    
    enabled = maintenance_setting and maintenance_setting.value == "true"
    return {"enabled": enabled}


@app.get("/api/settings/public")
async def get_public_settings(db: Session = Depends(get_db)):
    """Endpoint público para obter configurações do site"""
    settings = db.query(SiteSettings).filter(
        SiteSettings.category.in_(["theme", "content", "images"])
    ).all()
    
    settings_dict = {}
    for setting in settings:
        if setting.category not in settings_dict:
            settings_dict[setting.category] = {}
        settings_dict[setting.category][setting.key] = setting.value
    
    return settings_dict


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
