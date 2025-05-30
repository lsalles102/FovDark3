
import os

def is_railway_environment():
    """Verifica se está rodando no Railway"""
    return bool(
        os.getenv("RAILWAY_STATIC_URL") or 
        os.getenv("RAILWAY_PUBLIC_DOMAIN") or
        os.getenv("RAILWAY_ENVIRONMENT") or
        os.getenv("RAILWAY_PROJECT_ID")
    )

def get_railway_domain():
    """Obtém o domínio correto para Railway"""
    # Prioridade para domínio personalizado
    custom_domain = os.getenv("CUSTOM_DOMAIN")
    if custom_domain:
        return custom_domain.rstrip('/')
    
    # URL estática do Railway
    railway_static_url = os.getenv("RAILWAY_STATIC_URL")
    if railway_static_url:
        return railway_static_url.rstrip('/')
    
    # Domínio público do Railway
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_domain:
        return f"https://{railway_public_domain}"
    
    # Fallback para domínio personalizado
    return "https://www.fovdark.shop"

def get_railway_database_url():
    """Obtém a URL do banco de dados do Railway"""
    return os.getenv("DATABASE_URL")

def get_railway_port():
    """Obtém a porta do Railway"""
    return int(os.getenv("PORT", 5000))

def railway_environment_info():
    """Retorna informações do ambiente Railway"""
    return {
        "is_railway": is_railway_environment(),
        "domain": get_railway_domain(),
        "database_url_exists": bool(get_railway_database_url()),
        "port": get_railway_port(),
        "project_id": os.getenv("RAILWAY_PROJECT_ID"),
        "static_url": os.getenv("RAILWAY_STATIC_URL"),
        "public_domain": os.getenv("RAILWAY_PUBLIC_DOMAIN")
    }
