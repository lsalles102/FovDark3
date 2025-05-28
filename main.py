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
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [
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
    ]

@app.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).all()
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
            "features": product.features.split(',') if product.features else []
        }
        for product in products
    ]

@app.get("/api/admin/products")
async def get_admin_products(
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
            "created_at": product.created_at.isoformat() if product.created_at else None
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
    is_active: bool = Form(True),
    is_featured: bool = Form(False),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        new_product = Product(
            name=name,
            description=description,
            price=price,
            duration_days=duration_days,
            image_url=image_url if image_url else None,
            features=features if features else None,
            is_active=is_active,
            is_featured=is_featured
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {
            "message": "Produto criado com sucesso",
            "product": {
                "id": new_product.id,
                "name": new_product.name,
                "price": new_product.price,
                "duration_days": new_product.duration_days,
                "is_active": new_product.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")

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
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        product.name = name
        product.description = description
        product.price = price
        product.duration_days = duration_days
        product.image_url = image_url if image_url else None
        product.features = features if features else None
        product.is_active = is_active
        product.is_featured = is_featured

        db.commit()

        return {
            "message": "Produto atualizado com sucesso",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "duration_days": product.duration_days,
                "is_active": product.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")

@app.delete("/api/admin/products/{product_id}")
async def delete_product(
    product_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        db.delete(product)
        db.commit()
        return {"message": "Produto deletado com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar produto: {str(e)}")

@app.get("/api/license/check")
async def check_license(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verificar status da licença do usuário"""
    try:
        # Verificar se tem licença ativa
        has_active_license = current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow()
        
        if has_active_license:
            # Calcular tempo restante
            time_remaining = current_user.data_expiracao - datetime.utcnow()
            days_remaining = time_remaining.days
            
            # Determinar status baseado no tempo restante
            if days_remaining <= 1:
                status = "critico"
                message = f"Sua licença expira em {days_remaining} dia(s)"
            elif days_remaining <= 3:
                status = "expirando"
                message = f"Sua licença expira em {days_remaining} dias"
            elif days_remaining <= 7:
                status = "aviso"
                message = f"Sua licença expira em {days_remaining} dias"
            else:
                status = "ativa"
                message = f"Licença ativa por mais {days_remaining} dias"
            
            return {
                "valid": True,
                "can_download": True,
                "license_status": status,
                "message": message,
                "expires_at": current_user.data_expiracao.isoformat(),
                "email": current_user.email,
                "is_admin": current_user.is_admin
            }
        else:
            # Licença expirada ou inexistente
            status = "expirada" if current_user.data_expiracao else "sem_licenca"
            message = "Sua licença expirou" if current_user.data_expiracao else "Você não possui uma licença ativa"
            
            return {
                "valid": False,
                "can_download": False,
                "license_status": status,
                "message": message,
                "expires_at": current_user.data_expiracao.isoformat() if current_user.data_expiracao else None,
                "email": current_user.email,
                "is_admin": current_user.is_admin
            }
            
    except Exception as e:
        print(f"Erro ao verificar licença: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/admin/payments")
async def get_admin_payments(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).all()
    return [
        {
            "id": payment.id,
            "user_id": payment.user_id,
            "product_id": payment.product_id,
            "valor": payment.valor,
            "data_pagamento": payment.data_pagamento.isoformat() if payment.data_pagamento else None,
            "status": payment.status,
            "plano": payment.plano,
            "gateway_id": payment.gateway_id
        }
        for payment in payments
    ]

@app.get("/api/download/executable")
async def download_executable(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download do executável para usuários com licença ativa"""
    try:
        # Verificar se tem licença ativa
        has_active_license = current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow()
        
        if not has_active_license:
            raise HTTPException(status_code=403, detail="Licença inválida ou expirada")
        
        # Caminho para o arquivo executável
        executable_path = "attached_assets/Script_Dark.exe"
        
        if not os.path.exists(executable_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        return FileResponse(
            executable_path,
            media_type='application/octet-stream',
            filename="Script_Dark.exe"
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro no download: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/admin/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    try:
        # Verificar se é uma imagem
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")

        # Criar diretório se não existir
        import os
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Gerar nome único para o arquivo
        import time
        timestamp = int(time.time())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        new_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(upload_dir, new_filename)

        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Retornar URL da imagem
        image_url = f"/static/uploads/{new_filename}"

        return {
            "message": "Imagem enviada com sucesso",
            "image_url": image_url,
            "filename": new_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")

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