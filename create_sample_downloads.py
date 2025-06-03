
#!/usr/bin/env python3

from database import SessionLocal
from models import Download

def create_sample_downloads():
    db = SessionLocal()

    try:
        # Verificar se já existem downloads
        existing_downloads = db.query(Download).count()
        if existing_downloads > 0:
            print(f"✅ {existing_downloads} downloads já existem no banco")
            return

        # Criar downloads de exemplo
        downloads = [
            # Softwares
            {
                "title": "FPS Booster Pro",
                "description": "Otimizador avançado para aumentar FPS em jogos",
                "category": "software",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/fps-booster.exe",
                "file_size": "25 MB",
                "version": "2.1.0",
                "is_free": True,
                "price": 0.0,
                "is_active": True,
                "is_featured": True,
                "tags": "fps,booster,games,optimization",
                "requirements": "Windows 10/11, 4GB RAM"
            },
            {
                "title": "Registry Cleaner Ultimate",
                "description": "Limpador e otimizador do registro do Windows",
                "category": "software",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/registry-cleaner.exe",
                "file_size": "15 MB",
                "version": "1.5.2",
                "is_free": False,
                "price": 19.90,
                "is_active": True,
                "is_featured": False,
                "tags": "registry,cleaner,optimization,windows",
                "requirements": "Windows 7/8/10/11"
            },
            
            # ISOs
            {
                "title": "Windows 11 Gaming Edition",
                "description": "Windows 11 otimizado especialmente para jogos",
                "category": "iso",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/win11-gaming.iso",
                "file_size": "4.2 GB",
                "version": "22H2",
                "is_free": False,
                "price": 49.90,
                "is_active": True,
                "is_featured": True,
                "tags": "windows,gaming,optimized,performance",
                "requirements": "TPM 2.0, UEFI, 8GB RAM"
            },
            {
                "title": "Ubuntu Gaming Remix",
                "description": "Linux Ubuntu otimizado para gaming com drivers pré-instalados",
                "category": "iso",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/ubuntu-gaming.iso",
                "file_size": "3.8 GB",
                "version": "22.04",
                "is_free": True,
                "price": 0.0,
                "is_active": True,
                "is_featured": False,
                "tags": "ubuntu,linux,gaming,drivers",
                "requirements": "4GB RAM, 25GB de armazenamento"
            },
            
            # Otimizadores
            {
                "title": "PC Speed Maximizer",
                "description": "Otimizador completo para acelerar o Windows",
                "category": "optimizer",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/pc-speed.exe",
                "file_size": "32 MB",
                "version": "3.2.1",
                "is_free": True,
                "price": 0.0,
                "is_active": True,
                "is_featured": True,
                "tags": "speed,optimizer,windows,performance",
                "requirements": "Windows 10/11, 2GB RAM"
            },
            {
                "title": "Gaming Optimizer Pro",
                "description": "Otimizador premium para performance máxima em jogos",
                "category": "optimizer",
                "image_url": "/static/cyberpunk-soldier.jpg",
                "download_url": "https://example.com/gaming-optimizer.exe",
                "file_size": "45 MB",
                "version": "4.0.0",
                "is_free": False,
                "price": 29.90,
                "is_active": True,
                "is_featured": True,
                "tags": "gaming,optimizer,premium,performance",
                "requirements": "Windows 10/11, 8GB RAM"
            }
        ]

        # Criar downloads
        for download_data in downloads:
            download = Download(**download_data)
            db.add(download)

        db.commit()
        print("✅ 6 downloads de exemplo criados com sucesso!")

        # Listar downloads criados
        all_downloads = db.query(Download).all()
        print("\n📦 Downloads no banco:")
        for download in all_downloads:
            price_str = "GRÁTIS" if download.is_free else f"R$ {download.price}"
            print(f"   - [{download.category.upper()}] {download.title}: {price_str}")

    except Exception as e:
        print(f"❌ Erro ao criar downloads: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Criando downloads de exemplo...")
    create_sample_downloads()
    print("✅ Processo concluído!")
