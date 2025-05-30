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
import uvicorn
from collections import defaultdict
import time

from database import get_db, engine, Base
from models import User, Payment, Product, SiteSettings
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash, verify_password, decode_access_token
)
from mercadopago_routes import router as mercadopago_router
from license import create_payment_record, get_license_status
from admin import get_admin_user
from email_utils import send_confirmation_email, send_recovery_email

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FovDark - Sistema de Vendas", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mercadopago_router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    
    async def dispatch(self, request: Request, call_next):
        # Pular rate limiting para arquivos estáticos e admin
        if request.url.path.startswith("/static") or request.url.path.startswith("/admin"):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Limpar requisições antigas
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if now - req_time < self.period
        ]
        
        # Verificar se excedeu o limite
        if len(self.requests[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429, 
                detail="Muitas requisições. Tente novamente em alguns minutos."
            )
        
        # Adicionar requisição atual
        self.requests[client_ip].append(now)
        
        return await call_next(request)

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

app.add_middleware(RateLimitingMiddleware, calls=100, period=60)  # 100 req/min
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
    print(f"🔄 Tentativa de login recebida:")
    print(f"  📧 Email: {email}")
    print(f"  🌐 IP: {request.client.host if request.client else 'unknown'}")
    print(f"  📋 Headers: {dict(request.headers)}")
    
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
