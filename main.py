import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uvicorn
from collections import defaultdict
import time
import re

from database import get_db, engine, Base
from models import User, Payment, Product, SiteSettings, Download
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash, verify_password, decode_access_token, check_rate_limit, reset_rate_limit
)

def sanitize_input(text: str, max_length: int = 255) -> str:
    """Sanitizar entrada de texto"""
    if not text:
        return ""

    # Remover caracteres perigosos
    text = re.sub(r'[<>"\';\\]', '', str(text))

    # Limitar tamanho
    return text.strip()[:max_length]

def validate_email(email: str) -> bool:
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 255


from mercadopago_routes import router as mercadopago_router
from license import create_payment_record, get_license_status
from admin import get_admin_user
from email_utils import send_confirmation_email, send_recovery_email

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FovDark - Sistema de Vendas", version="1.0.0")

# Configurar CORS com restrições de segurança
allowed_origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://www.fovdark.shop",
    "https://fovdark.shop",
    "https://*.railway.app",
    "https://*.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=600,  # 10 minutos
)

app.include_router(mercadopago_router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Error handler for static files
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.url.path.startswith("/static/"):
        # Para arquivos JavaScript, retornar resposta JavaScript válida em caso de erro
        if request.url.path.endswith('.js'):
            return Response(
                content="console.error('Arquivo JavaScript não encontrado:', '" + request.url.path + "');",
                media_type="application/javascript; charset=utf-8",
                status_code=404
            )
        elif request.url.path.endswith('.css'):
            return Response(
                content="/* CSS file not found */",
                media_type="text/css; charset=utf-8", 
                status_code=404
            )
        return Response("File not found", status_code=404)
    return templates.TemplateResponse("error.html", {"request": request, "error": "Page not found"}, status_code=404)

security = HTTPBearer()

from pydantic import BaseModel

# Modelo Pydantic para HWID
class HWIDRequest(BaseModel):
    hwid: str

# Endpoint para salvar HWID
@app.post("/api/hwid/save")
async def save_hwid(
    hwid_data: HWIDRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not current_user.hwid:
            current_user.hwid = hwid_data.hwid
            db.commit()
            return {"message": "HWID salvo com sucesso"}

        if current_user.hwid != hwid_data.hwid:
            raise HTTPException(status_code=403, detail="Este usuário já está vinculado a outro dispositivo.")

        return {"message": "HWID já registrado"}

    except Exception as e:
        print(f"Erro ao salvar HWID: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno ao salvar HWID")


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = defaultdict(list)
        self.login_attempts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Pular rate limiting para arquivos estáticos
        if request.url.path.startswith("/static"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Rate limiting específico para login (mais restritivo)
        if request.url.path == "/api/login":
            # Limpar tentativas antigas de login
            self.login_attempts[client_ip] = [
                req_time for req_time in self.login_attempts[client_ip] 
                if now - req_time < 300  # 5 minutos
            ]

            # Máximo 5 tentativas de login por 5 minutos
            if len(self.login_attempts[client_ip]) >= 5:
                raise HTTPException(
                    status_code=429, 
                    detail="Muitas tentativas de login. Tente novamente em 5 minutos."
                )

            self.login_attempts[client_ip].append(now)

        # Rate limiting geral
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if now - req_time < self.period
        ]

        # Verificar se excedeu o limite geral
        if len(self.requests[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429, 
                detail="Muitas requisições. Tente novamente em alguns minutos."
            )

        # Adicionar requisição atual
        self.requests[client_ip].append(now)

        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Headers de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Content Security Policy
        if request.url.path.endswith('.html') or 'text/html' in response.headers.get('content-type', ''):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self' https://sdk.mercadopago.com https://www.mercadolibre.com https://static.cloudflareinsights.com https://www.fovdark.shop http://890ccd5f-759e-42f3-b6f0-5afa5d70af68-00-1imk31afnoo3x.riker.replit.dev; "
                "connect-src 'self' https://www.mercadolibre.com https://api.mercadopago.com https://fonts.googleapis.com https://static.cloudflareinsights.com https://www.fovdark.shop http://890ccd5f-759e-42f3-b6f0-5afa5d70af68-00-1imk31afnoo3x.riker.replit.dev; "
                "frame-src 'self' https://www.mercadolibre.com https://sdk.mercadopago.com https://www.fovdark.shop; "
                "script-src 'self' 'unsafe-inline' https://sdk.mercadopago.com https://cdnjs.cloudflare.com https://static.cloudflareinsights.com https://www.fovdark.shop http://890ccd5f-759e-42f3-b6f0-5afa5d70af68-00-1imk31afnoo3x.riker.replit.dev; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://www.fovdark.shop; "
                "img-src 'self' data: https: https://www.fovdark.shop; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://www.fovdark.shop; "
                "frame-ancestors 'none'"
            )

        # Set proper content type and headers for static files
        if request.url.path.endswith('.js'):
            response.headers['content-type'] = 'application/javascript; charset=utf-8'
            response.headers['cache-control'] = 'public, max-age=3600'
        elif request.url.path.endswith('.css'):
            response.headers['content-type'] = 'text/css; charset=utf-8'
            response.headers['cache-control'] = 'public, max-age=3600'
        elif request.url.path.startswith('/static/'):
            response.headers['cache-control'] = 'public, max-age=86400'

        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitingMiddleware, calls=50, period=60)  # 50 req/min (mais restritivo)

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
    # Validação e sanitização do email
    email = email.strip().lower()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email inválido")

    if len(email) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email muito longo")

    # Validação da senha
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha deve ter pelo menos 8 caracteres")

    if len(password) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha muito longa")

    if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha deve conter letras e números")

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
    # Validação e sanitização básica
    email = email.strip().lower()
    if not email or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email e senha são obrigatórios")

    if len(email) > 255 or len(password) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dados inválidos")

    # Log de segurança (sem expor dados sensíveis)
    client_ip = request.client.host if request.client else 'unknown'
    print(f"🔄 Tentativa de login - IP: {client_ip}")

    try:
        # Rate limiting removido para melhor debugging

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

        # Rate limit reset removido

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
        print(f"❌ HTTP Exception no login: {he.detail}")
        raise he
    except Exception as e:
        print(f"💥 Erro crítico no login: {str(e)}")
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

# ===== API ENDPOINTS =====

@app.get("/api/settings/public")
async def get_public_settings():
    """Endpoint para configurações públicas"""
    return {
        "site_name": "FovDark",
        "version": "1.0.0",
        "maintenance_mode": False
    }

@app.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    try:
        print("🔍 Carregando produtos do banco de dados...")
        products = db.query(Product).filter(Product.is_active == True).all()
        print(f"📊 Encontrados {len(products)} produtos ativos")

        products_data = []
        for product in products:
            try:
                product_dict = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description or "",
                    "price": float(product.price) if product.price else 0.0,
                    "duration_days": product.duration_days or 30,
                    "image_url": product.image_url or "",
                    "is_active": product.is_active,
                    "is_featured": product.is_featured or False,
                    "features": product.features.split(',') if product.features else []
                }
                products_data.append(product_dict)
                print(f"✅ Produto processado: {product.name}")
            except Exception as product_error:
                print(f"❌ Erro ao processar produto {product.id}: {product_error}")
                continue

        print(f"🎯 Retornando {len(products_data)} produtos")
        return products_data

    except Exception as e:
        print(f"❌ Erro no endpoint /api/products: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

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
    is_active: str = Form("true"),
    is_featured: str = Form("false"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"📝 Criando produto: {name}")
        print(f"💰 Preço: {price}")
        print(f"📅 Duração: {duration_days} dias")
        print(f"🔗 Imagem URL: {image_url}")
        print(f"✅ Ativo: {is_active}")
        print(f"⭐ Destaque: {is_featured}")

        # Converter strings para boolean
        is_active_bool = is_active.lower() in ('true', '1', 'on', 'yes')
        is_featured_bool = is_featured.lower() in ('true', '1', 'on', 'yes')

        new_product = Product(
            name=name.strip(),
            description=description.strip() if description else None,
            price=float(price),
            duration_days=int(duration_days),
            image_url=image_url.strip() if image_url else None,
            features=features.strip() if features else None,
            is_active=is_active_bool,
            is_featured=is_featured_bool
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        print(f"✅ Produto criado com ID: {new_product.id}")

        return {
            "message": "Produto criado com sucesso",
            "product": {
                "id": new_product.id,
                "name": new_product.name,
                "description": new_product.description,
                "price": new_product.price,
                "duration_days": new_product.duration_days,
                "image_url": new_product.image_url,
                "is_active": new_product.is_active,
                "is_featured": new_product.is_featured,
                "features": new_product.features
            }
        }
    except ValueError as ve:
        print(f"❌ Erro de valor: {ve}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro nos dados fornecidos: {str(ve)}")
    except Exception as e:
        print(f"❌ Erro ao criar produto: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.put("/api/admin/products/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    duration_days: int = Form(...),
    image_url: str = Form(""),
    features: str = Form(""),
    is_active: str = Form("true"),
    is_featured: str = Form("false"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    print(f"🔄 Recebendo atualização para produto ID: {product_id}")
    print(f"📝 Dados recebidos para atualização:")
    print(f"  Nome: '{name}'")
    print(f"  Descrição: '{description}'")
    print(f"  Preço: {price}")
    print(f"  Duração: {duration_days} dias")
    print(f"  URL da imagem: '{image_url}'")
    print(f"  Recursos: '{features}'")
    print(f"  Ativo: '{is_active}'")
    print(f"  Destaque: '{is_featured}'")

    # Verificar se o produto existe
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        print(f"❌ Produto {product_id} não encontrado no banco de dados")
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    print(f"✅ Produto encontrado: '{product.name}' (ID: {product.id})")
    print(f"📊 Estado atual do produto:")
    print(f"  Nome atual: '{product.name}'")
    print(f"  Preço atual: {product.price}")
    print(f"  Ativo atual: {product.is_active}")

    try:
        # Validar dados de entrada
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Nome do produto é obrigatório")

        if price < 0:
            raise HTTPException(status_code=400, detail="Preço deve ser maior ou igual a zero")

        if duration_days <= 0:
            raise HTTPException(status_code=400, detail="Duração deve ser maior que zero")

        # Converter strings para boolean de forma mais robusta
        is_active_bool = str(is_active).lower() in ('true', '1', 'on', 'yes', 'active')
        is_featured_bool = str(is_featured).lower() in ('true', '1', 'on', 'yes', 'featured')

        print(f"🔄 Convertendo valores:")
        print(f"  is_active '{is_active}' -> {is_active_bool}")
        print(f"  is_featured '{is_featured}' -> {is_featured_bool}")

        # Salvar valores antigos para log
        old_values = {
            "name": product.name,
            "price": product.price,
            "is_active": product.is_active,
            "is_featured": product.is_featured
        }

        # Atualizar campos do produto
        product.name = name.strip()
        product.description = description.strip() if description and description.strip() else None
        product.price = float(price)
        product.duration_days = int(duration_days)
        product.image_url = image_url.strip() if image_url and image_url.strip() else None
        product.features = features.strip() if features and features.strip() else None
        product.is_active = is_active_bool
        product.is_featured = is_featured_bool
        product.updated_at = datetime.utcnow()

        print(f"🔄 Atualizando produto no banco de dados...")
        print(f"📊 Mudanças:")
        print(f"  Nome: '{old_values['name']}' -> '{product.name}'")
        print(f"  Preço: {old_values['price']} -> {product.price}")
        print(f"  Ativo: {old_values['is_active']} -> {product.is_active}")
        print(f"  Destaque: {old_values['is_featured']} -> {product.is_featured}")

        # Commit das mudanças
        db.commit()
        db.refresh(product)

        print(f"✅ Produto {product_id} atualizado com sucesso no banco!")
        print(f"📊 Estado final:")
        print(f"  Nome: '{product.name}'")
        print(f"  Preço: {product.price}")
        print(f"  Ativo: {product.is_active}")

        response_data = {
            "message": "Produto atualizado com sucesso",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "duration_days": product.duration_days,
                "image_url": product.image_url,
                "is_active": product.is_active,
                "is_featured": product.is_featured,
                "features": product.features,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
        }

        print(f"📤 Retornando resposta: {response_data}")
        return response_data

    except ValueError as ve:
        print(f"❌ Erro de valor: {ve}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro nos dados fornecidos: {str(ve)}")
    except HTTPException as he:
        print(f"❌ HTTP Exception: {he.detail}")
        db.rollback()
        raise he
    except Exception as e:
        print(f"❌ Erro ao atualizar produto: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

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
        print(f"🔍 Verificando licença para usuário: {current_user.email}")
        print(f"📅 Data de expiração no banco: {current_user.data_expiracao}")
        print(f"📊 Status licença no banco: {current_user.status_licenca}")

        # Verificar se tem data de expiração
        now = datetime.utcnow()

        if not current_user.data_expiracao:
            # Verificar se há pagamentos pendentes
            pending_payment = db.query(Payment).filter(
                Payment.user_id == current_user.id,
                Payment.status.in_(["pending", "processing"])
            ).first()

            if pending_payment:
                status = "pendente"
                message = "Aguardando confirmação do pagamento"
                print(f"💳 Pagamento pendente encontrado: {pending_payment.id}")
            else:
                status = "sem_licenca"
                message = "Você não possui uma licença ativa"

            response = {
                "valid": False,
                "can_download": False,
                "license_status": status,
                "message": message,
                "expires_at": None,
                "days_remaining": 0,
                "hours_remaining": 0,
                "email": current_user.email,
                "is_admin": current_user.is_admin or False
            }
            print(f"📤 Resposta (sem licença): {response}")
            return response

        # Verificar se a licença está ativa baseada na data de expiração
        if current_user.data_expiracao > now:
            # Atualizar status no banco se necessário
            if current_user.status_licenca != "ativa":
                print(f"🔄 Atualizando status da licença de '{current_user.status_licenca}' para 'ativa'")
                current_user.status_licenca = "ativa"
                db.commit()

            # Licença ativa - calcular tempo restante
            time_remaining = current_user.data_expiracao - now
            days_remaining = time_remaining.days
            hours_remaining = time_remaining.seconds // 3600

            print(f"📅 Data de expiração: {current_user.data_expiracao}")
            print(f"⏰ Tempo restante: {days_remaining} dias, {hours_remaining} horas")

            # Determinar status baseado no tempo restante
            if days_remaining == 0 and hours_remaining <= 24:
                status = "critico"
                message = f"Sua licença expira em {hours_remaining} horas"
            elif days_remaining <= 1:
                status = "critico"
                message = f"Sua licença expira em {days_remaining} dia e {hours_remaining} horas"
            elif days_remaining <= 3:
                status = "expirando"
                message = f"Sua licença expira em {days_remaining} dias"
            elif days_remaining <= 7:
                status = "aviso"
                message = f"Sua licença expira em {days_remaining} dias"
            else:
                status = "ativa"
                message = f"Licença ativa por mais {days_remaining} dias"

            response = {
                "valid": True,
                "can_download": True,
                "license_status": status,
                "message": message,
                "expires_at": current_user.data_expiracao.isoformat(),
                "days_remaining": days_remaining,
                "hours_remaining": hours_remaining,
                "email": current_user.email,
                "is_admin": current_user.is_admin or False
            }
            print(f"📤 Resposta (licença ativa): {response}")
            return response
        else:
            # Atualizar status no banco para expirada se necessário
            if current_user.status_licenca != "expirada":
                print(f"🔄 Atualizando status da licença de '{current_user.status_licenca}' para 'expirada'")
                current_user.status_licenca = "expirada"
                db.commit()

            # Licença expirada
            expired_days = (now - current_user.data_expiracao).days

            response = {
                "valid": False,
                "can_download": False,
                "license_status": "expirada",
                "message": f"Sua licença expirou há {expired_days} dias",
                "expires_at": current_user.data_expiracao.isoformat(),
                "days_remaining": 0,
                "hours_remaining": 0,
                "expired_days": expired_days,
                "email": current_user.email,
                "is_admin": current_user.is_admin or False
            }
            print(f"📤 Resposta (licença expirada): {response}")
            return response

    except Exception as e:
        print(f"❌ Erro ao verificar licença: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

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

# ===== DOWNLOADS API ENDPOINTS =====

@app.get("/api/downloads/{category}")
async def get_downloads_by_category(category: str, db: Session = Depends(get_db)):
    """Obter downloads por categoria"""
    try:
        valid_categories = ['software', 'iso', 'optimizer']
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail="Categoria inválida")

        downloads = db.query(Download).filter(
            Download.category == category,
            Download.is_active == True
        ).order_by(Download.is_featured.desc(), Download.created_at.desc()).all()

        downloads_data = []
        for download in downloads:
            download_dict = {
                "id": download.id,
                "title": download.title,
                "description": download.description,
                "category": download.category,
                "image_url": download.image_url,
                "file_size": download.file_size,
                "version": download.version,
                "is_free": download.is_free,
                "price": float(download.price) if download.price else 0.0,
                "download_count": download.download_count,
                "is_featured": download.is_featured,
                "tags": download.tags,
                "requirements": download.requirements,
                "created_at": download.created_at.isoformat() if download.created_at else None
            }
            downloads_data.append(download_dict)

        return downloads_data

    except Exception as e:
        print(f"❌ Erro no endpoint /api/downloads/{category}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.post("/api/downloads/{download_id}/download")
async def download_file(
    download_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processar download de arquivo"""
    try:
        download = db.query(Download).filter(Download.id == download_id).first()
        if not download:
            raise HTTPException(status_code=404, detail="Download não encontrado")

        if not download.is_active:
            raise HTTPException(status_code=403, detail="Download não disponível")

        # Se for pago, verificar se o usuário tem licença ativa
        if not download.is_free:
            has_active_license = current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow()
            if not has_active_license:
                raise HTTPException(status_code=403, detail="Licença necessária para downloads pagos")

        # Incrementar contador de downloads
        download.download_count += 1
        db.commit()

        # Retornar arquivo ou URL de download
        if download.download_url:
            return {"download_url": download.download_url, "message": "Download iniciado"}
        else:
            # Se não tiver URL, simular download direto
            return {"message": "Download processado com sucesso"}

    except Exception as e:
        print(f"❌ Erro no download {download_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/api/admin/downloads")
async def get_admin_downloads(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Obter todos os downloads para administração"""
    downloads = db.query(Download).order_by(Download.created_at.desc()).all()
    return [
        {
            "id": download.id,
            "title": download.title,
            "description": download.description,
            "category": download.category,
            "image_url": download.image_url,
            "download_url": download.download_url,
            "file_size": download.file_size,
            "version": download.version,
            "is_free": download.is_free,
            "price": download.price,
            "download_count": download.download_count,
            "is_active": download.is_active,
            "is_featured": download.is_featured,
            "tags": download.tags,
            "requirements": download.requirements,
            "created_at": download.created_at.isoformat() if download.created_at else None,
            "updated_at": download.updated_at.isoformat() if download.updated_at else None
        }
        for download in downloads
    ]

@app.post("/api/admin/downloads")
async def create_download(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    image_url: str = Form(""),
    download_url: str = Form(""),
    file_size: str = Form(""),
    version: str = Form(""),
    is_free: str = Form("true"),
    price: float = Form(0.0),
    tags: str = Form(""),
    requirements: str = Form(""),
    is_active: str = Form("true"),
    is_featured: str = Form("false"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Criar novo download"""
    try:
        valid_categories = ['software', 'iso', 'optimizer']
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail="Categoria inválida")

        is_free_bool = is_free.lower() in ('true', '1', 'on', 'yes')
        is_active_bool = is_active.lower() in ('true', '1', 'on', 'yes')
        is_featured_bool = is_featured.lower() in ('true', '1', 'on', 'yes')

        new_download = Download(
            title=title.strip(),
            description=description.strip() if description else None,
            category=category,
            image_url=image_url.strip() if image_url else None,
            download_url=download_url.strip() if download_url else None,
            file_size=file_size.strip() if file_size else None,
            version=version.strip() if version else None,
            is_free=is_free_bool,
            price=float(price) if not is_free_bool else 0.0,
            tags=tags.strip() if tags else None,
            requirements=requirements.strip() if requirements else None,
            is_active=is_active_bool,
            is_featured=is_featured_bool
        )

        db.add(new_download)
        db.commit()
        db.refresh(new_download)

        return {
            "message": "Download criado com sucesso",
            "download": {
                "id": new_download.id,
                "title": new_download.title,
                "category": new_download.category,
                "is_free": new_download.is_free,
                "price": new_download.price
            }
        }
    except Exception as e:
        print(f"❌ Erro ao criar download: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.put("/api/admin/downloads/{download_id}")
async def update_download(
    download_id: int,
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    image_url: str = Form(""),
    download_url: str = Form(""),
    file_size: str = Form(""),
    version: str = Form(""),
    is_free: str = Form("true"),
    price: float = Form(0.0),
    tags: str = Form(""),
    requirements: str = Form(""),
    is_active: str = Form("true"),
    is_featured: str = Form("false"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Atualizar download existente"""
    try:
        download = db.query(Download).filter(Download.id == download_id).first()
        if not download:
            raise HTTPException(status_code=404, detail="Download não encontrado")

        valid_categories = ['software', 'iso', 'optimizer']
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail="Categoria inválida")

        is_free_bool = is_free.lower() in ('true', '1', 'on', 'yes')
        is_active_bool = is_active.lower() in ('true', '1', 'on', 'yes')
        is_featured_bool = is_featured.lower() in ('true', '1', 'on', 'yes')

        download.title = title.strip()
        download.description = description.strip() if description else None
        download.category = category
        download.image_url = image_url.strip() if image_url else None
        download.download_url = download_url.strip() if download_url else None
        download.file_size = file_size.strip() if file_size else None
        download.version = version.strip() if version else None
        download.is_free = is_free_bool
        download.price = float(price) if not is_free_bool else 0.0
        download.tags = tags.strip() if tags else None
        download.requirements = requirements.strip() if requirements else None
        download.is_active = is_active_bool
        download.is_featured = is_featured_bool
        download.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(download)

        return {
            "message": "Download atualizado com sucesso",
            "download": {
                "id": download.id,
                "title": download.title,
                "category": download.category,
                "is_active": download.is_active
            }
        }
    except Exception as e:
        print(f"❌ Erro ao atualizar download: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.delete("/api/admin/downloads/{download_id}")
async def delete_download(
    download_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Deletar download"""
    try:
        download = db.query(Download).filter(Download.id == download_id).first()
        if not download:
            raise HTTPException(status_code=404, detail="Download não encontrado")

        db.delete(download)
        db.commit()

        return {"message": "Download deletado com sucesso"}
    except Exception as e:
        print(f"❌ Erro ao deletar download: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")



@app.get("/api/download/loader")
async def download_loader(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download do FovDarkloader.exe para usuários com licença ativa"""
    try:
        # Verificar se tem licença ativa
        has_active_license = current_user.data_expiracao and current_user.data_expiracao > datetime.utcnow()

        if not has_active_license:
            raise HTTPException(status_code=403, detail="Licença inválida ou expirada")

        # Caminho para o arquivo loader
        loader_path = "FovDarkloader.exe"

        if not os.path.exists(loader_path):
            raise HTTPException(status_code=404, detail="FovDark Loader não encontrado")

        return FileResponse(
            loader_path,
            media_type='application/octet-stream',
            filename="FovDarkloader.exe"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erro no download do loader: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/admin/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    try:
        # Verificar se é uma imagem
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")

        # Verificar tamanho do arquivo (máximo 5MB para melhor performance)
        if not file.size or file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5MB")

        # Verificar se o arquivo tem nome válido
        if not file.filename or len(file.filename.strip()) == 0:
            raise HTTPException(status_code=400, detail="Nome do arquivo inválido")

        # Criar diretório se não existir
        import os
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Gerar nome único para o arquivo
        import time
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]

        # Obter extensão do arquivo
        if file.filename and '.' in file.filename:
            file_extension = file.filename.split('.')[-1].lower()
        else:
            file_extension = 'jpg'

        # Validar extensão
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Formato de imagem não suportado")

        # Criar nome único do arquivo
        safe_filename = f"{timestamp}_{unique_id}.{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)

        # Salvar arquivo
        try:
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        except Exception as write_error:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(write_error)}")

        # Retornar URL da imagem
        image_url = f"/static/uploads/{safe_filename}"

        print(f"✅ Upload realizado com sucesso: {image_url}")

        return {
            "message": "Imagem enviada com sucesso",
            "image_url": image_url,
            "filename": safe_filename,
            "size": file.size,
            "content_type": file.content_type
        }
    except HTTPException as he:
        print(f"❌ Erro HTTP no upload: {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ Erro geral no upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

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

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Página de política de privacidade"""
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Página de termos de uso"""
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/secure-checkout", response_class=HTMLResponse)
async def secure_checkout_page(request: Request):
    """Página de checkout seguro com Secure Fields"""
    return templates.TemplateResponse("secure_checkout.html", {"request": request})

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    """Página de pagamento bem-sucedido"""
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/cancelled", response_class=HTMLResponse)
async def cancelled_page(request: Request):
    """Página de pagamento cancelado"""
    return templates.TemplateResponse("cancelled.html", {"request": request})

@app.get("/pending", response_class=HTMLResponse)
async def pending_page(request: Request):
    """Página de pagamento pendente"""
    return templates.TemplateResponse("pending.html", {"request": request})

@app.get("/recover", response_class=HTMLResponse)
async def recover_page(request: Request):
    return templates.TemplateResponse("recover.html", {"request": request})

@app.post("/api/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alterar senha do usuário"""
    try:
        # Verificar senha atual
        if not verify_password(current_password, current_user.senha_hash):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")

        # Validar nova senha
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 8 caracteres")

        # Verificar se a nova senha é diferente da atual
        if verify_password(new_password, current_user.senha_hash):
            raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da atual")

        # Atualizar senha
        current_user.senha_hash = get_password_hash(new_password)
        current_user.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "Senha alterada com sucesso"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Erro ao alterar senha: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.post("/api/verify_token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verificar se o token é válido"""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "is_admin": current_user.is_admin
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/test-mercadopago")
async def test_mercadopago():
    """Testar configuração do MercadoPago"""
    try:
        from mercadopago_integration import MERCADOPAGO_ACCESS_TOKEN, mp, get_domain

        if not MERCADOPAGO_ACCESS_TOKEN:
            return {
                "status": "error",
                "message": "Token do MercadoPago não configurado",
                "solution": "Configure MERCADOPAGO_ACCESS_TOKEN nos Secrets"
            }

        if not mp:
            return {
                "status": "error", 
                "message": "SDK do MercadoPago não inicializado",
                "solution": "Verifique se o token está correto"
            }

        # Testar criação de uma preferência simples
        test_preference = {
            "items": [{
                "title": "Teste",
                "quantity": 1,
                "unit_price": 1.00,
                "currency_id": "BRL"
            }],
            "back_urls": {
                "success": f"{get_domain()}/success",
                "failure": f"{get_domain()}/cancelled",
                "pending": f"{get_domain()}/pending"
            }
        }

        try:
            test_response = mp.preference().create(test_preference)
            if test_response["status"] == 201:
                return {
                    "status": "success",
                    "message": "MercadoPago configurado corretamente",
                    "environment": "TEST" if "TEST" in MERCADOPAGO_ACCESS_TOKEN else "PRODUCTION",
                    "domain": get_domain()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Erro na API: Status {test_response['status']}",
                    "details": test_response.get("response", {})
                }
        except Exception as api_error:
            return {
                "status": "error",
                "message": f"Erro na comunicação com API: {str(api_error)}",
                "solution": "Verifique se o token está correto e se não expirou"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro interno: {str(e)}"
        }

@app.get("/api/debug/payment-config")
async def debug_payment_config():
    """Debug da configuração de pagamentos"""
    try:
        import os
        from mercadopago_integration import MERCADOPAGO_ACCESS_TOKEN, mp, get_domain

        config_info = {
            "mercadopago_configured": bool(MERCADOPAGO_ACCESS_TOKEN),
            "token_type": "TEST" if MERCADOPAGO_ACCESS_TOKEN and "TEST" in MERCADOPAGO_ACCESS_TOKEN else "PRODUCTION" if MERCADOPAGO_ACCESS_TOKEN else "NONE",
            "token_prefix": MERCADOPAGO_ACCESS_TOKEN[:20] + "..." if MERCADOPAGO_ACCESS_TOKEN else "NONE",
            "sdk_initialized": bool(mp),
            "domain": get_domain(),
            "webhook_url": f"{get_domain()}/api/webhook/mercadopago",
            "environment_vars": {
                "MERCADOPAGO_ACCESS_TOKEN": "CONFIGURADO" if MERCADOPAGO_ACCESS_TOKEN else "NÃO CONFIGURADO",
                "PORT": os.getenv("PORT", "5000"),
                "DATABASE_URL": "CONFIGURADO" if os.getenv("DATABASE_URL") else "NÃO CONFIGURADO",
                "CUSTOM_DOMAIN": os.getenv("CUSTOM_DOMAIN", "NÃO CONFIGURADO"),
                "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL", "NÃO CONFIGURADO"),
                "RAILWAY_PUBLIC_DOMAIN": os.getenv("RAILWAY_PUBLIC_DOMAIN", "NÃO CONFIGURADO"),
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NÃO CONFIGURADO"),
                "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID", "NÃO CONFIGURADO")
            }
        }

        return config_info

    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/railway")
async def debug_railway():
    """Debug específico para Railway"""
    try:
        import os
        from railway_config import is_railway_environment, get_railway_domain

        debug_info = {
            "platform_detected": "Railway" if is_railway_environment() else "Other",
            "is_railway": is_railway_environment(),
            "railway_domain": get_railway_domain() if is_railway_environment() else "N/A",
            "all_env_vars": {
                "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL"),
                "RAILWAY_PUBLIC_DOMAIN": os.getenv("RAILWAY_PUBLIC_DOMAIN"), 
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
                "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID"),
                "RAILWAY_SERVICE_NAME": os.getenv("RAILWAY_SERVICE_NAME"),
                "RAILWAY_PROJECT_NAME": os.getenv("RAILWAY_PROJECT_NAME"),
                "CUSTOM_DOMAIN": os.getenv("CUSTOM_DOMAIN"),
                "PORT": os.getenv("PORT"),
                "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT_SET"
            }
        }

        return debug_info

    except Exception as e:
        return {"error": str(e), "traceback": str(e)}

@app.get("/api/debug/payments")
async def debug_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug de pagamentos do usuário"""
    try:
        # Buscar pagamentos do usuário
        user_payments = db.query(Payment).filter(
            Payment.user_id == current_user.id
        ).order_by(Payment.data_pagamento.desc()).all()

        # Buscar todos os produtos disponíveis
        products = db.query(Product).filter(Product.is_active == True).all()

        return {
            "user_info": {
                "id": current_user.id,
                "email": current_user.email,
                "license_expires": current_user.data_expiracao.isoformat() if current_user.data_expiracao else None,
                "license_status": current_user.status_licenca
            },
            "payments": [
                {
                    "id": p.id,
                    "product_id": p.product_id,
                    "valor": p.valor,
                    "status": p.status,
                    "plano": p.plano,
                    "gateway_id": p.gateway_id,
                    "data_pagamento": p.data_pagamento.isoformat() if p.data_pagamento else None
                }
                for p in user_payments
            ],
            "available_products": [
                {
                    "id": prod.id,
                    "name": prod.name,
                    "price": prod.price,
                    "duration_days": prod.duration_days,
                    "is_active": prod.is_active
                }
                for prod in products
            ]
        }

    except Exception as e:
        print(f"❌ Erro no debug de pagamentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/mercadopago/public-key")
async def get_mercadopago_public_key():
    """Obter chave pública do MercadoPago"""
    try:
        from mercadopago_integration import MERCADOPAGO_ACCESS_TOKEN

        if not MERCADOPAGO_ACCESS_TOKEN:
            raise HTTPException(status_code=500, detail="MercadoPago não configurado")

        # Extrair chave pública do token de acesso
        # Para tokens de teste: TEST-xxx -> public key
        # Para tokens de produção: APP_USR-xxx -> public key correspondente
        if "TEST-" in MERCADOPAGO_ACCESS_TOKEN:
            # Para ambiente de teste, usar chave pública de teste
            public_key = "TEST-a8b1e4f8-e4a5-4b1c-9c8d-2e3f4g5h6i7j"
        else:
            # Para produção, você precisaria configurar a chave pública real
            # Por enquanto, usar uma chave de teste como fallback
            public_key = "TEST-a8b1e4f8-e4a5-4b1c-9c8d-2e3f4g5h6i7j"

        return {
            "public_key": public_key,
            "environment": "test" if "TEST-" in MERCADOPAGO_ACCESS_TOKEN else "production"
        }

    except Exception as e:
        print(f"❌ Erro ao obter chave pública: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/api/mercadopago/status")
async def mercadopago_status():
    """Verificar status da integração do MercadoPago"""
    try:
        from mercadopago_integration import MERCADOPAGO_ACCESS_TOKEN, mp, get_domain
        from railway_config import is_railway_environment

        # Debug das variáveis de ambiente
        import os
        debug_info = {
            "platform": "Railway" if is_railway_environment() else "Replit" if os.getenv("REPL_SLUG") else "Other",
            "custom_domain": os.getenv("CUSTOM_DOMAIN"),
            "railway_static_url": os.getenv("RAILWAY_STATIC_URL"),
            "railway_public_domain": os.getenv("RAILWAY_PUBLIC_DOMAIN"),
            "railway_environment": os.getenv("RAILWAY_ENVIRONMENT"),
            "railway_project_id": os.getenv("RAILWAY_PROJECT_ID"),
            "port": os.getenv("PORT"),
            "mercadopago_token_exists": bool(MERCADOPAGO_ACCESS_TOKEN),
            "calculated_domain": get_domain()
        }

        if not MERCADOPAGO_ACCESS_TOKEN:
            platform_name = "Railway" if is_railway_environment() else "Replit"
            return {
                "status": "not_configured",
                "message": "❌ MercadoPago NÃO configurado",
                "instructions": f"Configure MERCADOPAGO_ACCESS_TOKEN nas variáveis do {platform_name}",
                "environment": "none",
                "can_process_payments": False,
                "platform": platform_name,
                "debug": debug_info,
                "suggestions": [
                    f"1. Acesse o painel do {platform_name}",
                    "2. Adicione a variável MERCADOPAGO_ACCESS_TOKEN",
                    "3. Configure CUSTOM_DOMAIN se necessário",
                    "4. Redeploy a aplicação"
                ]
            }

        if mp:
            is_production = "TEST" not in MERCADOPAGO_ACCESS_TOKEN
            domain = get_domain()

            return {
                "status": "configured",
                "message": f"✅ MercadoPago configurado em modo {'PRODUÇÃO' if is_production else 'TESTE'}",
                "environment": "production" if is_production else "test",
                "can_process_payments": True,
                "payments_real": is_production,
                "token_prefix": MERCADOPAGO_ACCESS_TOKEN[:20] + "..." if len(MERCADOPAGO_ACCESS_TOKEN) > 20 else "***",
                "webhook_url": f"{domain}/api/webhook/mercadopago",
                "checkout_urls": {
                    "success": f"{domain}/success",
                    "failure": f"{domain}/cancelled", 
                    "pending": f"{domain}/pending"
                },
                "domain_issues": {
                    "domain_valid": domain.startswith('https://'),
                    "domain_accessible": not domain.startswith('http://localhost'),
                    "webhook_reachable": domain.startswith('https://')
                },
                "debug": debug_info
            }
        else:
            return {
                "status": "error",
                "message": "❌ Erro na inicialização do MercadoPago",
                "environment": "error",
                "can_process_payments": False,
                "debug": debug_info,
                "possible_causes": [
                    "Token do MercadoPago inválido",
                    "Problema na conectividade",
                    "SDK do MercadoPago não instalado"
                ]
            }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"❌ Erro ao verificar MercadoPago: {str(e)}",
            "environment": "unknown",
            "can_process_payments": False,
            "debug": {"error": str(e), "traceback": traceback.format_exc()}
        }

@app.get("/softwares", response_class=HTMLResponse)
async def softwares_page(request: Request):
    """Página de softwares"""
    return templates.TemplateResponse("softwares.html", {"request": request})

@app.get("/isos", response_class=HTMLResponse)
async def isos_page(request: Request):
    """Página de ISOs otimizadas"""
    return templates.TemplateResponse("isos.html", {"request": request})

@app.get("/otimizadores", response_class=HTMLResponse)
async def otimizadores_page(request: Request):
    """Página de otimizadores"""
    return templates.TemplateResponse("otimizadores.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)