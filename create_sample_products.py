#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import Product

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)

def create_sample_products():
    db = SessionLocal()

    try:
        # Verificar se já existem produtos
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print(f"✅ {existing_products} produtos já existem no banco")
            return

        # Produtos de exemplo
        products = [
            {
                "name": "FovDark Basic",
                "description": "Pacote básico com recursos essenciais para iniciantes",
                "price": 29.90,
                "duration_days": 30,
                "image_url": "/static/cyberpunk-soldier.jpg",
                "features": "Aimbot Básico,ESP Player,Anti-Cheat Básico,Suporte 24h",
                "is_active": True,
                "is_featured": False
            },
            {
                "name": "FovDark Pro",
                "description": "Pacote completo para jogadores intermediários",
                "price": 79.90,
                "duration_days": 90,
                "image_url": "/static/cyberpunk-sniper.jpg",
                "features": "Aimbot Avançado,ESP Completo,Wallhack,Anti-Cheat Pro,No Recoil,Radar Hack,Suporte VIP",
                "is_active": True,
                "is_featured": True
            },
            {
                "name": "FovDark Elite",
                "description": "Pacote premium com todos os recursos disponíveis",
                "price": 199.90,
                "duration_days": 365,
                "image_url": "/static/hero-bg.jpg", 
                "features": "Todos os recursos Pro,Custom Config,Bypass Atualizado,HWID Spoofer,Stream Mode,Configs Personalizadas,Suporte Premium 24/7",
                "is_active": True,
                "is_featured": True
            }
        ]

        # Criar produtos
        for product_data in products:
            product = Product(**product_data)
            db.add(product)

        db.commit()
        print("✅ 3 produtos de exemplo criados com sucesso!")

        # Listar produtos criados
        all_products = db.query(Product).all()
        print("\n📦 Produtos no banco:")
        for product in all_products:
            print(f"   - {product.name}: R$ {product.price} ({product.duration_days} dias)")

    except Exception as e:
        print(f"❌ Erro ao criar produtos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Criando produtos de exemplo...")
    create_sample_products()