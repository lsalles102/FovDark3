
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Product
from datetime import datetime

# Criar todas as tabelas
Base.metadata.create_all(bind=engine)

def create_sample_products():
    db = SessionLocal()
    
    try:
        # Verificar se já existem produtos
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print(f"Já existem {existing_products} produtos no banco")
            return
        
        # Produtos de exemplo
        products = [
            Product(
                name="FovDark Mensal",
                description="Acesso completo ao FovDark por 30 dias",
                price=29.90,
                duration_days=30,
                image_url="/static/cyberpunk-soldier.jpg",
                is_active=True,
                is_featured=False,
                features="Aim Assist Inteligente, Anti-Detecção, Suporte Discord, Atualizações Gratuitas"
            ),
            Product(
                name="FovDark Trimestral",
                description="Acesso completo ao FovDark por 90 dias com desconto",
                price=79.90,
                duration_days=90,
                image_url="/static/cyberpunk-soldier.jpg",
                is_active=True,
                is_featured=True,
                features="Tudo do plano mensal, Configurações Premium, Suporte Prioritário, Acesso Antecipado"
            ),
            Product(
                name="FovDark Anual",
                description="Acesso completo ao FovDark por 365 dias - melhor valor",
                price=199.90,
                duration_days=365,
                image_url="/static/cyberpunk-soldier.jpg",
                is_active=True,
                is_featured=False,
                features="Tudo dos planos anteriores, Recursos Exclusivos, Suporte VIP 24/7, Acesso vitalício a updates"
            )
        ]
        
        # Adicionar produtos ao banco
        for product in products:
            db.add(product)
        
        db.commit()
        print("✓ Produtos de exemplo criados com sucesso!")
        
        # Listar produtos criados
        all_products = db.query(Product).all()
        for product in all_products:
            print(f"- {product.name}: R$ {product.price} ({product.duration_days} dias)")
            
    except Exception as e:
        print(f"Erro ao criar produtos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_products()
