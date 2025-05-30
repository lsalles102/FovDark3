
import os
from railway_config import get_railway_domain, is_railway_environment

def get_production_domain():
    """Retorna o domínio de produção configurado para Railway"""
    if is_railway_environment():
        return get_railway_domain()
    
    # Fallback para desenvolvimento local
    return "http://localhost:5000"

def get_webhook_url():
    """Retorna a URL completa do webhook para o MercadoPago"""
    domain = get_production_domain()
    return f"{domain}/api/webhook/mercadopago"

def get_success_urls():
    """Retorna as URLs de redirecionamento após pagamento"""
    domain = get_production_domain()
    return {
        "success": f"{domain}/success",
        "failure": f"{domain}/cancelled", 
        "pending": f"{domain}/pending"
    }

def get_cors_origins():
    """Retorna as origens permitidas para CORS no Railway"""
    domain = get_production_domain()
    return [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        domain,
        "https://www.fovdark.shop",
        "https://fovdark.shop",
        "https://*.railway.app",
        "https://*.up.railway.app"
    ]
