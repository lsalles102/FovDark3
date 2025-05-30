
from database import get_db
from models import Product
from datetime import datetime

def create_sample_products():
    """Criar produtos de exemplo"""
    db = next(get_db())
    
    # Verificar se já existem produtos
    existing = db.query(Product).first()
    if existing:
        print("✅ Produtos já existem no banco")
        db.close()
        return
    
    # Criar produtos de exemplo
    products = [
        {
            "name": "FovDark Basic - 30 dias",
            "description": "Acesso básico ao FovDark por 30 dias",
            "price": 29.90,
            "duration_days": 30,
            "is_active": True,
            "is_featured": False,
            "features": "Aimbot,ESP,Wallhack"
        },
        {
            "name": "FovDark Premium - 30 dias",
            "description": "Acesso premium ao FovDark por 30 dias com recursos extras",
            "price": 49.90,
            "duration_days": 30,
            "is_active": True,
            "is_featured": True,
            "features": "Aimbot,ESP,Wallhack,Anti-ban,Suporte VIP"
        },
        {
            "name": "FovDark Lifetime",
            "description": "Acesso vitalício ao FovDark",
            "price": 199.90,
            "duration_days": 3650,  # 10 anos
            "is_active": True,
            "is_featured": True,
            "features": "Aimbot,ESP,Wallhack,Anti-ban,Suporte VIP,Updates grátis"
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print("✅ Produtos de exemplo criados!")
    db.close()

if __name__ == "__main__":
    create_sample_products()
